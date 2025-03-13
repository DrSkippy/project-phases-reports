import csv
import datetime

from reports.configurations import CSS_STYLE

PROJECT_PATH = "/Users/s.hendrickson/Documents/OneDrive - F5, Inc/Projects Folders/3-In Progress/Data Team KPIs Dashboard"
FILENAME = "/MetricsDefinition.csv"
TABLE_ALL = ['Base:Team', 'Metric Information:Component', 'Metric Information:Priority', 'Metric Information:Owner', 'Metric Information:Name', 'Metric Information:Description', 'Metric Information:Update Frequency', 'Metric Information:Historical Data', 'Metric Information:Calculation Formula', 'Metric Information:Availability', 'Metric Information:Units', 'Metric Information:Version', 'Range:Minimum Value', 'Range:Maximum Value', 'Range:Goal Value', 'Threshold 1:Threshold', 'Threshold 1:Action', 'Threshold 2:Threshold', 'Threshold 2:Action', 'Threshold 3:Threshold', 'Threshold 3:Action', 'Data 1:Name', 'Data 1:Source of Truth', 'Data 1:Update Frequency', 'Data 1:Minimum', 'Data 1:Maximum', 'Data 1:Units', 'Data 1:Availability', 'Data 1:Automation', 'Data 1:Granularity', 'Data 2:Name', 'Data 2:Source of Truth', 'Data 2:Update Frequency', 'Data 2:Minimum', 'Data 2:Maximum', 'Data 2:Units', 'Data 2:Availability', 'Data 2:Automation', 'Data 2:Granularity', 'Data 3:Name', 'Data 3:Source of Truth', 'Data 3:Update Frequency', 'Data 3:Minimum', 'Data 3:Maximum', 'Data 3:Units', 'Data 3:Availability', 'Data 3:Automation', 'Data 3:Granularity', 'Data 4:Name', 'Data 4:Source of Truth', 'Data 4:Update Frequency', 'Data 4:Minimum', 'Data 4:Maximum', 'Data 4:Units', 'Data 4:Availability', 'Data 4:Granularity', 'Data 5:Name', 'Data 5:Source of Truth', 'Data 5:Update Frequency', 'Data 5:Minimum', 'Data 5:Maximum', 'Data 5:Units', 'Data 5:Availability', 'Data 5:Granularity']
TABLE1 = [
'Metric Information:Component',
'Metric Information:Name',
'Metric Information:Description',
'Metric Information:Calculation Formula',
'Data 1:Name',
'Data 1:Source of Truth',
'Data 2:Name',
'Data 2:Source of Truth'
] 


def metric_html_tables(mdict, keys):
    res = []
    res.append(CSS_STYLE)
    m = mdict[0]
    template_row = ('<tr>'
                    f'<td colspan=1 rowspan=1>{m["Base:Team"]}</td>'
                    f'<td colspan=1 rowspan=1>{m["Base:Team"]}</td>'
                    f'<td colspan=1 rowspan=1>{m["Base:Team"]}</td>'
                    f'<td colspan=1 rowspan=1>{m["Base:Team"]}</td>'
                    f'<td colspan=1 rowspan=1>{m["Base:Team"]}</td>'
                    f'<td colspan=1 rowspan=1>{m["Base:Team"]}</td>'
                    '</tr>')
    for m in mdict:
        # how many data columns are filled out?
        data_cols = [f"Data {i}" for i in range(1,5)]
        data_name_cols = [f"{i}:Name" for i in data_cols]
        n_data = sum([x in keys for x in data_name_cols if m[x] != ""])
        # new table for each metric
        res.append(f'<h2> Metric Name: {m["Metric Information:Name"]}</h2>')
        res.append('<table border=0.1>')
        res.append(('<tr class="tr-owner">'
                   f'<td colspan=1>Name:</td>'
                   f'<td colspan=3>{m["Metric Information:Name"]}</td>'
                   f'<td colspan=1>Date:</td>'
                   f'<td colspan=1>{str(datetime.datetime.now())[:11]} (Ver. {m["Metric Information:Version"]}) </td>'
                    '</tr>'))
        res.append(('<tr>'
                    f'<td colspan=1 rowspan=1>Owner:</td>'
                    f'<td colspan=1 rowspan=1>{m["Metric Information:Owner"]}</td>'
                    f'<td colspan=4 rowspan=3>{m["Metric Information:Description"]}</td>'
                    '</tr>'))
        res.append(('<tr>'
                    f'<td colspan=1 rowspan=1>Available:</td>'
                    f'<td colspan=1 rowspan=1>{m["Metric Information:Availability"]}</td>'
                    '</tr>'))
        res.append(('<tr>'
                    f'<td colspan=1 rowspan=1>Goal Value:</td>'
                    f'<td colspan=1 rowspan=1>{m["Range:Goal Value"]}</td>'
                    '</tr>'))
        res.append(('<tr>'
                    f'<td colspan=1 rowspan=1>Units:</td>'
                    f'<td colspan=1 rowspan=1>{m["Metric Information:Units"]}</td>'
                    f'<td colspan=4 rowspan=3>{m["Metric Information:Calculation Formula"]}</td>'
                    '</tr>'))        
        res.append(('<tr>'
                    f'<td colspan=1 rowspan=1>Minimum Value:</td>'
                    f'<td colspan=1 rowspan=1>{m["Range:Minimum Value"]}</td>'
                    '</tr>'))
        res.append(('<tr>'
                    f'<td colspan=1 rowspan=1>Maximum Value:</td>'
                    f'<td colspan=1 rowspan=1>{m["Range:Maximum Value"]}</td>'
                    '</tr>'))

        for i in range(n_data):
            key = data_cols[i]
            name_key = ":".join([key, "Name"])
            availability_key = ":".join([key, "Availability"])
            units_key = ":".join([key, "Units"])
            max_key = ":".join([key, "Maximum"])
            min_key = ":".join([key, "Minimum"])
            sot_key = ":".join([key, "Source of Truth"])
            automation_key = ":".join([key, "Automation"])
            #
            res.append(('<tr class="tr-project">'
                    f'<td colspan=1 rowspan=1>Required Data</td>'
                    f'<td colspan=1 rowspan=1>{m[name_key]}</td>'
                    f'<td colspan=4 rowspan=3>{m[sot_key]}</td>'
                    '</tr>'))
            res.append(('<tr>'
                    f'<td colspan=1 rowspan=1></td>'
                        f'<td colspan=1 rowspan=1>Available: {m[availability_key]}</td>'
                    '</tr>'))
            res.append(('<tr>'
                    f'<td colspan=1 rowspan=1></td>'
                    f'<td colspan=1 rowspan=1>Units: {m[units_key]}</td>'
                    '</tr>'))
            res.append(('<tr>'
                    f'<td colspan=1 rowspan=1></td>'
                    f'<td colspan=1 rowspan=1></td>'
                    f'<td colspan=2 rowspan=1>Data Range:</td>'
                    f'<td colspan=1 rowspan=1>{m[min_key]}</td>'
                    f'<td colspan=1 rowspan=1>{m[max_key]}</td>'
                    '</tr>'))
        res.append('</table>')
    return "\n".join(res)

def fetch_csv(path):
    with open(path, mode='r', encoding='utf-8-sig') as infile:
        metrics = []
        reader = csv.reader(infile)
        for row in reader:
            metrics.append(row)

    # make keys from first two rows
    keys = []
    prefix = "Base"
    for i, m1 in enumerate(metrics[0]):
        if m1 is not None and m1 != "":
            prefix = m1
        keys.append(prefix+":"+metrics[1][i])
    # make dict
    metric_dicts = []
    for i in range(2,len(metrics)):
        if metrics[i][4] != "":
            metric_dicts.append({keys[j]: metrics[i][j] for j in range(len(keys))})
    return metric_dicts, keys


def simple_html_table(mdict, keys):
    res = [] 
    res.append(CSS_STYLE)
    res.append("<h2> Metrics Table </h2>")
    res.append("<table>")
    row = '<tr class="tr-owner"><th> ' + ' </th><th> '.join(keys) + ' </th><tr>'
    res.append(row)
    for m in mdict:
        row = '<tr><td> ' + ' </td><td> '.join([f'{m[k]}' for k in keys]) + ' </td><tr>'
        res.append(row)
    res.append("</table>")
    return "\n".join(res)


def make_key_list(keys):
    print(keys)


if __name__ == "__main__":
    mdefs, keys = fetch_csv(PROJECT_PATH + FILENAME)
    # # make_key_list(keys)
    # mdts = simple_html_table(mdefs, TABLE1)
    # with open(PROJECT_PATH + "/simple_table.html", "w") as ofile1:
    #     ofile1.write(mdts)
    # mdt = metric_html_tables(mdefs, keys)
    # with open(PROJECT_PATH + "/metric_table.html", "w") as ofile2:
    #     ofile2.write(mdt)
