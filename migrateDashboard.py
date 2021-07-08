import json
import jinja2
import os
import argparse


def get_dashboard_metadata(dashboard: dict, override_metadata=None):
    if override_metadata is None:
        override_metadata = {}

    # Pick keys :
    metadata = {
        "style": "dark",
        "tags": [],
        "time_from": dashboard['time']['from'] or 'now-3h',
        "time_to": dashboard['time']['to'] or 'now',
        "refresh": '60s',
        "timezone": "browser",
    }

    keys = ["editable", "graphTooltip", "refresh", "style", "tags", "timepicker", "timezone", "title"]
    for key, value in dashboard.items():
        if key in keys:
            metadata.update({
                key: value
            })
    metadata.update(override_metadata)

    return metadata


def render_jinja(template_path, dashboard_metadata, templates, panels, **kwargs):
    env = jinja2.Environment(loader=jinja2.FileSystemLoader('templates'))
    dashboard_template = env.get_template(template_path)
    rendered_dashboard_jsonnet = dashboard_template.render(dashboard_metadata=dashboard_metadata,
                                                           templates=templates,
                                                           panels=panels,
                                                           **kwargs)
    return rendered_dashboard_jsonnet


def get_templates(dashboard: dict):
    templates = []
    common = ["hide", "name", "query", "regex", "type"]
    keys = {
        "datasource": common + ['current'],
        'interval': ['hide', 'name', 'query', 'label', 'type', 'current'],
        "query": common + ["datasource", "label", "multi", "sort"],
        "custom": common + ['label', 'type', 'multi', 'valuelabels', 'current']
    }
    if 'templating' in dashboard.keys():
        for template in dashboard['templating']['list']:
            default_template = {
            }
            for k, v in template.items():
                if k in keys[template['type']]:
                    if k == 'current':
                        default_template.update({
                            k: v['value']
                        })
                    else:
                        default_template.update(
                            {k: v}
                        )
            templates.append(default_template)
    return templates


def get_panels(dashboard: dict):
    panels = []
    common = ['title', 'transparent', 'span', 'description', 'type']
    panel_type = {
        'alertlist': common + [],
        'graph': common + ['bar', 'datasource', 'fill', 'fillGradient', 'percentage', 'pointradius',
                           'points', 'stack', 'targets', 'nullPointMode'],
        'barGauge': common + [],
        'gauge': common + ['transparent', 'colors', 'datasource', 'targets'],
        'heatmap': common + ['datasource', 'dataFormat', 'hideZeroBuckets', 'highlightCards',
                             'repeatDirection', 'targets',
                             'stack'],
        'log': common + [],
        'pieChart': common + [],
        'row': common + ['collapse'],
        'stat': common + ['datasource', 'targets'],
        'singlestat': common + ['internval', 'datasource', 'height', 'valueName', 'valueFontSize'
                                                                                  'mappingType', "targets"],
        'table': common + ['columns', 'height', 'datasource', 'sort', 'transform', 'styles', 'targets'],
        'text': common + ['content', 'mode', 'datasource'],
    }
    if 'panels' in dashboard.keys():
        for panel in dashboard['panels']:
            # TODO Get more defaults based on type
            if panel['type'] == 'graph':
                default_panel = {
                    "x_axis_buckets": panel["xaxis"]["buckets"],
                    "x_axis_mode": panel["xaxis"]["mode"],
                    "x_axis_values": panel["xaxis"]["values"],
                    "legend_avg": panel["legend"]["avg"],
                    "legend_current": panel["legend"]["current"],
                    "legend_max": panel["legend"]["max"],
                    "legend_min": panel["legend"]["min"],
                    "legend_show": panel["legend"]["show"],
                    "legend_total": panel["legend"]["total"],
                    "legend_values": panel["legend"]["values"],
                }
                # TODO convert this mess in  addYaxis(format,min,max,label,show,logBase,decimals)
                _ = 0
                for y in panel['yaxes']:
                    _ += 1
                    default_panel.update({
                        "formatY{}".format(_): y['format'],
                        "labelY{}".format(_): y['format'],
                        "min".format(_): y['min'],
                        "max".format(_): y['max'],
                    })
            elif panel['type'] == 'heatmap':
                default_panel = {
                    "cards_cardPadding": panel["cards"]["cardPadding"],
                    "cards_cardRound": panel["cards"]["cardRound"],
                    "color_cardColor": panel["color"]["cardColor"],
                    "color_colorScale": panel["color"]["colorScale"],
                    "color_colorScheme": panel["color"]["colorScheme"],
                    "color_exponent": panel["color"]["exponent"],
                    "color_mode": panel["color"]["mode"],
                    "yAxis_decimals": panel["yAxis"]["decimals"],
                    "yAxis_format": panel["yAxis"]["format"],
                    "yAxis_logBase": panel["yAxis"]["logBase"],
                    "yAxis_max": panel["yAxis"]["max"],
                    "yAxis_min": panel["yAxis"]["min"],
                    "yAxis_show": panel["yAxis"]["show"],
                    "yAxis_splitFactor": panel["yAxis"]["splitFactor"]
                }
            elif panel['type'] == 'singlestat':
                default_panel = {
                    "sparklineFillColor": panel["sparkline"]["fillColor"],
                    "sparklineFull": panel["sparkline"]["full"],
                    "sparklineLineColor": panel["sparkline"]["lineColor"],
                    "sparklineShow": panel["sparkline"]["show"]
                }
            elif panel['type'] == 'table':
                default_panel = {}
            elif panel['type'] == 'row':
                if 'panels' in panel:
                    default_panel = {
                        'panels': get_panels({
                            "panels": panel['panels']
                        })
                    }
                else:
                    default_panel = {}
            elif panel['type'] == 'gauge':
                default_panel = {
                    "unit": panel["fieldConfig"]['defaults']["unit"],
                    "min": panel["fieldConfig"]['defaults']["min"],
                    "max": panel["fieldConfig"]['defaults']["max"],
                    "thresholdsMode": panel["fieldConfig"]['defaults']["thresholds"]["mode"],
                    "thresholds": [],
                    "mappings": [],
                }
                for t in panel["fieldConfig"]['defaults']["thresholds"]["steps"]:
                    c = {}
                    for k, v in t.items():
                        c.update({k: v})
                    default_panel['thresholds'].append(c)
                for t in panel["fieldConfig"]['defaults']["mappings"]:
                    c = {}
                    for k, v in t.items():
                        # if k == 'op':
                        #     c.update({"operator": v)}
                        if k == 'id':
                            continue
                        c.update({k: v})
                    c.pop('op')
                    default_panel['mappings'].append(c)
            elif panel['type'] == 'stat':
                default_panel = {
                    "thresholdsMode": panel["fieldConfig"]['defaults']["thresholds"]["mode"],
                    "thresholds": [],
                    "mappings": [],
                    'colorMode': panel["options"]['colorMode'],
                    'graphMode': panel["options"]['graphMode'],
                    'justifyMode': panel["options"]['justifyMode'],
                    'orientation': panel["options"]['orientation'],
                }
                default_panel['thresholds'] = panel["fieldConfig"]['defaults']["thresholds"]["steps"]
                # for t in panel["fieldConfig"]['defaults']["thresholds"]["steps"]:
                #     c = {}
                #     for k, v in t.items():
                #         c.update({k: v})
                #     default_panel['thresholds'].append(c)

                for t in panel["fieldConfig"]['defaults']["mappings"]:
                    c = {}
                    for k, v in t.items():
                        if k == 'id':
                            continue
                        c.update({k: v})
                    c.pop('op')
                    default_panel['mappings'].append(c)

            else:
                default_panel = {}
            for k, v in default_panel.items():
                default_panel[k] = v
            for k, v in panel.items():
                if k in panel_type[panel['type']]:
                    if k == 'targets':
                        default_panel['targets'] = []
                        t: dict
                        v: list
                        for t in v:
                            for k in ['refId', 'step', 'metric', 'queryType']:
                                try:
                                    t.pop(k)
                                except KeyError:
                                    pass
                            default_panel['targets'].append(
                                t
                            )
                    elif k == 'columns':
                        default_panel['columns'] = []
                        s: dict
                        v: list
                        for s in v:
                            default_panel['columns'].append(
                                {'field': s['text'], 'style': {}}
                            )
                    elif k == 'styles':
                        default_panel['styles'] = []
                        s: dict
                        v: list
                        for s in v:
                            default_panel['styles'].append(
                                s
                            )
                    else:
                        default_panel.update(
                            {k: v}
                        )
            panels.append(default_panel)
    return panels


# TODO Get Annotations included
def get_annotations(dashboard: dict):
    raise NotImplementedError


def get_types(dashboard):
    t = []
    if 'panels' in dashboard.keys():
        for p in dashboard['panels']:
            if p['type'] == 'row':
                t.append('row')
                t.extend(get_types(p))
            else:
                t.append(p['type'])
    return list(set(t))


def load_dashboards(file):
    with open(file, 'r') as f:
        dashboard = json.load(f)
        return dashboard


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Migrate Grafana Dashboards to jsonnet.')
    parser.add_argument('--dir','-d',required=True,help='path for dashboard directory')

    args = parser.parse_args()
    for file in os.listdir(args.dir):
        if file.endswith('.json'):
            dashboard_json = os.path.abspath(args.dir + '/'+ file)
            d = load_dashboards(dashboard_json)
            metadata = get_dashboard_metadata(d)
            t = get_templates(d)
            p = get_panels(d)
            ty = get_types(d)
            r = render_jinja('dashboard_template.jinja2', metadata, t, p,
                             dashboard_name=file.split('.')[0].title().replace('-', ''), import_list=ty)
            with open('{}'.format(dashboard_json.replace('.json', '.jsonnet')), 'w') as f:
                f.write(r)
