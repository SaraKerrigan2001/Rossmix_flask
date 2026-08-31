import openpyxl
import os

def generate_html():
    wb = openpyxl.load_workbook('docs/Rossmix_Documentacion_Completa.xlsx')
    sheet = wb['Casos Prueba']
    
    modules = {}
    current_module = None
    headers = []
    
    for row in sheet.iter_rows(min_row=5, values_only=True):
        if not any(row):
            continue
            
        first_cell = str(row[0]).strip() if row[0] else ""
        
        if "MÓDULO" in first_cell or "M\u00d3DULO" in first_cell or "MDULO" in first_cell:
            current_module = first_cell.replace("MDULO:", "MÓDULO:").replace("M\u00d3DULO:", "MÓDULO:").strip()
            modules[current_module] = []
            continue
            
        if first_cell == "ID":
            headers = [str(x) if x else "" for x in row]
            continue
            
        if current_module and first_cell and first_cell != "None":
            # Add row to current module
            modules[current_module].append([str(x) if x is not None else "" for x in row])
            
    html_content = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Casos de Prueba - Rossmix</title>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7f6; padding: 20px; }
            h1 { text-align: center; color: #333; margin-bottom: 30px; }
            .container { display: flex; flex-wrap: nowrap; gap: 20px; overflow-x: auto; padding-bottom: 20px; align-items: flex-start; }
            .module-card { background: white; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); padding: 20px; min-width: 600px; flex: 0 0 auto; }
            .module-title { font-size: 1.2rem; font-weight: bold; color: #ff1493; margin-bottom: 15px; border-bottom: 2px solid #ff1493; padding-bottom: 5px; }
            table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
            th, td { padding: 8px 12px; border: 1px solid #ddd; text-align: left; }
            th { background-color: #f8f9fa; font-weight: 600; color: #555; }
            tr:nth-child(even) { background-color: #fbfbfb; }
            .priority-Alta { color: #d97706; font-weight: bold; }
            .priority-Media { color: #2563eb; font-weight: bold; }
            .priority-Baja { color: #059669; font-weight: bold; }
            .priority-Crítica, .priority-Critica { color: #dc2626; font-weight: bold; }
            .status-ok { color: #16a34a; font-weight: bold; }
        </style>
    </head>
    <body>
        <h1>Casos de Prueba por Módulo</h1>
        <div class="container">
    """
    
    for module_name, cases in modules.items():
        if not cases: continue
        html_content += f'<div class="module-card"><div class="module-title">{module_name}</div>'
        html_content += '<table><thead><tr>'
        for h in headers:
            html_content += f'<th>{h}</th>'
        html_content += '</tr></thead><tbody>'
        
        for case in cases:
            html_content += '<tr>'
            for i, val in enumerate(case):
                css_class = ""
                if i == 2: # Priority
                    css_class = f' class="priority-{val}"'
                elif i == 6 and "\u2705" in val:
                    css_class = ' class="status-ok"'
                html_content += f'<td{css_class}>{val}</td>'
            html_content += '</tr>'
            
        html_content += '</tbody></table></div>'
        
    html_content += """
        </div>
    </body>
    </html>
    """
    
    with open('docs/casos_prueba_vista.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
        
    print("HTML generado exitosamente en docs/casos_prueba_vista.html")

if __name__ == '__main__':
    generate_html()
