from click import style
import dash
import dash_html_components as html 
from simple_salesforce import Salesforce
import dash_core_components as dcc
from dash.dependencies import Input, Output
import pandas as pd
from datetime import timedelta
import dash_auth 
import plotly.express as px

USERNAME_PASSWORD_PAIRS=[['salesforce','awesome']] ## arbitrary credentials to app
today_naive = pd.to_datetime('today')

### definint constants###
background_color = "#E7EFF8"

def tile_style_c():
    tile_style = {
    'border':'4px solid white', 
    'background': 'white',
    'width':'200px',
    'border-radius': '25px',
    'margin': '5px',
    'border-shadow' : '200px 200px 55px black'}
    return tile_style
    

stage_remap = {'new' : 'New Order', 
               'test' : 'Test', 
               'sched_pickup' : 'Scheduling Pickup', 
               'Waiting for package' : 'Waiting for Package', 
               'invoicing_payment' : 'Invoicing', 
               'Paid and waiting for export' : 'Ready for export', 
               'complete' : 'Completed', 
               'canceled' : 'Failed', 
               'waiting_for_package' : 'Waiting for Package', 
               'waiting_for_material' : 'Waiting for Material', 
               'exported' : 'Exported', 
               'scheduling_pickup' : 'Scheduling Pickup', 
               'completed' : 'Completed', 
               'waiting_for_spedition' : 'Waiting for Transport', 
               'quote_required' : 'Quote Required', 
               'paid_for_export' : 'Paid for Export', 
               'buffer' : 'Payment in progress', 
               '101' : 'Reclamation', 
               'IBAN / Verification' : 'IBAN/verification', 
               'waiting_for_wiegeschein' : 'Waiting for Weight Note', 
               '100' : 'New Order',
               'New transaction' : 'New Order', 
               'failed' : 'Failed'}
stage_category_order = {
               0:'New Order', 
               1:'Scheduling Pickup',
               2:'Scheduling Pickup', 
               3:'Waiting for Transport',
               4:'Waiting for Weight Note',
               5:'Reclamation', 
               6:'Ready for export', 
               7:'Payment in progress', 
               8:'Exported',
               9:'Invoicing',                
               10:'Waiting for Material'}

data_items = stage_category_order.items()
data_list = list(data_items)
stage_category_order_df = pd.DataFrame(data_list)
stage_category_order_df['Status__c'] = stage_category_order_df.iloc[:,1]
stage_category_order_df['Index'] = stage_category_order_df.iloc[:,0]
stage_category_order_df.drop([0,1], axis=1, inplace=True)


#To access the information from an Org, create a file in this repository
#with three lines: username, password and salesforce token

with open('salesforce_login.txt') as f:
    username, password, token = [x.strip("\n") for x in f.readlines()]
sf = Salesforce(username=username, password=password, security_token=token)

def is_today (df, column):
    df[column] = pd.to_datetime(df[column])
    df[column + '_year'] = df[column].dt.year
    df[column + '_month'] = df[column].dt.month
    df[column + '_day'] = df[column].dt.day
    year = pd.to_datetime('today').year
    month = pd.to_datetime('today').month
    day = pd.to_datetime('today').day
    todays_df = df[(df[column + '_year'] == year) & (df[column + '_month'] == month) & (df[column + '_day'] == day)]
    return todays_df


app = dash.Dash()
auth =dash_auth.BasicAuth(app, USERNAME_PASSWORD_PAIRS)
server = app.server

app.layout = html.Div([
                html.H1('Daily Operations Dashboard'),
                html.Div(children=[   
                    html.Div(children=[
                        html.Div(children=[
                            html.Div(children=[
                                html.H3('New orders today'),
                                html.H1(id='live-update-text',style={'textAlign': 'center'})],
                                style=tile_style_c()),
                            html.Div(children=[
                                html.H3('Moved orders today'),
                                html.H1(id='moved-orders',style={'textAlign': 'center'})],            
                                style=tile_style_c()),
                            html.Div(children=[
                                html.H3('Stuck orders'),
                                html.H1(id='stuck-orders',style={'textAlign': 'center'})],            
                                style=tile_style_c()),
                            html.Div(children=[
                                html.H3('Claim orders'),
                                html.H1(id='claim-orders',style={'textAlign': 'center'})],           
                                style=tile_style_c())
                                ])
                    ]),
                        dcc.Graph(id='funnel'),
                        html.Div(children=[
                            html.Div(children=[
                                html.Div(children=[
                                    html.H3('# of Scheduled Pickups'),
                                    html.H2(id='WSF_orders',style={'textAlign': 'center'})],
                                    style=tile_style_c()),
                                html.Div(children=[
                                    html.H3('GMV of Scheduled Pickups'),
                                    html.H2(id='WSF_orders_gmv')],
                                    style=tile_style_c())],
                            style={'display':'flex'}),
                            html.Div(children=[
                                html.Div(children=[
                                    html.H3('# of Delivered orders today'),
                                    html.H2(id='delivered_orders',style={'textAlign': 'center'})],
                                    style=tile_style_c()),
                                html.Div(children=[
                                    html.H3('GMV of Delivered orders today'),
                                    html.H2(id='delivered_orders_gmv')],
                                    style=tile_style_c())],
                            style={'display':'flex'}),
                            html.Div(children=[
                                html.Div(children=[
                                    html.H3('# of Invoiced orders today'),
                                    html.H2(id='invoiced_orders',style={'textAlign': 'center'})],
                                    style=tile_style_c()),
                                html.Div(children=[
                                    html.H3('GMV of Invoiced orders today'),
                                    html.H2(id='invoiced_orders_gmv')],
                                    style=tile_style_c())],
                            style={'display':'flex'}),
                            html.Div(children=[
                                html.Div(children=[
                                    html.H3('# of Completed orders today'),
                                    html.H2(id='completed_orders',style={'textAlign': 'center'})],
                                    style=tile_style_c()),
                                html.Div(children=[
                                    html.H3('GMV of Completed orders today'),
                                    html.H2(id='completed_orders_gmv')],
                                    style=tile_style_c())],
                            style={'display':'flex'})
                        ])
                ],style={'display':'flex'}),
                dcc.Interval(id='interval-component',
                            interval=15000,
                            n_intervals=0)
                    ],
            style={'background':background_color})
                    
@app.callback(Output('live-update-text', 'children'),
              Input('interval-component', 'n_intervals'))

def update_new_orders(n):
    query = "SELECT Name, TotalMargin__c, Age__c, Status__c FROM Order__c WHERE Status__c IN ('new', '100', 'overseas') AND Age__c = 0 AND RecordTypeId = '01209000000xizgAAA'"
    orders = sf.query_all(query)
    orders = pd.DataFrame(orders['records']).drop(columns='attributes')
    total_orders = orders.Name.count()
    return total_orders

@app.callback(Output('moved-orders', 'children'),
              Input('interval-component', 'n_intervals'))

def update_moved_orders(n):
    global today_naive
    query = "SELECT Name, TotalMargin__c, Age__c, Status__c, Status_change_date__c FROM Order__c WHERE Status__c IN ('scheduling_pickup', 'waiting_for_spedition', 'waiting_for_wiegeschein', '101', 'paid_for_export', 'buffer', 'waiting_for_material', 'waiting_for_package', 'IBAN / Verification', 'paid_for_export_paypal') AND RecordTypeId = '01209000000xizgAAA'"
    orders = sf.query_all(query)
    orders = pd.DataFrame(orders['records']).drop(columns='attributes')
    orders.loc[:,'status_age'] = today_naive - pd.to_datetime(orders.loc[:,'Status_change_date__c'])
    moved_status = orders[orders['status_age'] < timedelta(days=1)]
    number_moved_orders_today = moved_status.Name.count()

    return number_moved_orders_today


@app.callback(Output('stuck-orders', 'children'),
              Input('interval-component', 'n_intervals'))

def update_stuck_orders(n):
    global today_naive
    query = "SELECT Name, TotalMargin__c, Age__c, Status__c, Status_change_date__c FROM Order__c WHERE Status__c IN ('new', 'scheduling_pickup', 'waiting_for_spedition', 'waiting_for_wiegeschein', '101', 'invoicing_payment', 'paid_for_export', 'buffer', 'waiting_for_material', 'waiting_for_package', 'IBAN / Verification', 'paid_for_export_paypal') AND RecordTypeId = '01209000000xizgAAA'"
    orders = sf.query_all(query)
    orders = pd.DataFrame(orders['records']).drop(columns='attributes')
    orders.loc[:,'status_age'] = today_naive - pd.to_datetime(orders.loc[:,'Status_change_date__c'])
    stuck_status = orders[orders['status_age'] > timedelta(days=7)]
    stuck_orders = stuck_status.Name.count()
    return stuck_orders


@app.callback(Output('claim-orders', 'children'),
              Input('interval-component', 'n_intervals'))

def update_claim_orders(n):
    query = "SELECT Name, Status__c FROM Order__c WHERE Status__c = '101'"
    orders = sf.query_all(query)
    orders = pd.DataFrame(orders['records']).drop(columns='attributes')
    claim_orders = orders.Name.count()
    return claim_orders

@app.callback(Output('funnel', 'figure'),
              Input('interval-component', 'n_intervals'))

def update_funnel(n):
    global stage_remap
    global stage_category_order_df
    query = "SELECT Name, Status__c FROM Order__c WHERE Status__c NOT IN  ('test', 'completed', 'failed', 'canceled', '1', 'overseas') AND RecordTypeId = '01209000000xizgAAA'"
    orders = sf.query_all(query)
    orders = pd.DataFrame(orders['records']).drop(columns='attributes')
    orders = orders.replace({'Status__c': stage_remap})
    summary_per_stage = orders.groupby('Status__c').count().sort_values(by='Name', ascending=False)
    summary_per_stage = pd.merge(summary_per_stage, 
                        stage_category_order_df, 
                        on ='Status__c', 
                        how ='inner')
    summary_per_stage = summary_per_stage.sort_values(by='Index', ascending=True)
    summary_per_stage.drop(['Index'], axis=1, inplace=True)
    summary_per_stage.set_index('Status__c')
    data = pd.Series(summary_per_stage.Name.values,index=summary_per_stage.Status__c).to_dict()
    funnel_fig = px.funnel(x=data.values(), y=data.keys(), category_orders=stage_category_order)
    return funnel_fig

@app.callback(Output('WSF_orders', 'children'),
              Input('interval-component', 'n_intervals'))

def update_WSF_count(n):
    query = "SELECT Name, Status__c, Status_change_date__c FROM Order__c WHERE Status__c = 'waiting_for_spedition' AND RecordTypeId = '01209000000xizgAAA'"
    orders = sf.query_all(query)
    orders = pd.DataFrame(orders['records']).drop(columns='attributes')
    orders.loc[:,'status_age'] = today_naive - pd.to_datetime(orders.loc[:,'Status_change_date__c'])
    WSF_status = orders[orders['status_age'] < timedelta(days=1)]
    WSF_orders = WSF_status.Name.count()
    return WSF_orders

@app.callback(Output('WSF_orders_gmv', 'children'),
              Input('interval-component', 'n_intervals'))

def update_WSF_GMV(n):
    query = "SELECT Name, Status__c, Sale_Value__c, Status_change_date__c FROM Order__c WHERE Status__c = 'waiting_for_spedition' AND RecordTypeId = '01209000000xizgAAA'"
    orders = sf.query_all(query)
    orders = pd.DataFrame(orders['records']).drop(columns='attributes')
    orders.loc[:,'status_age'] = today_naive - pd.to_datetime(orders.loc[:,'Status_change_date__c'])
    WSF_status = orders[orders['status_age'] < timedelta(days=1)]
    WSF_orders_GMV = round(WSF_status.Sale_Value__c.sum()/1000,1)
    WSF_orders_GMV = 'EUR ' + str(WSF_orders_GMV) + 'k'
    return WSF_orders_GMV

@app.callback(Output('delivered_orders', 'children'),
              Input('interval-component', 'n_intervals'))

def update_delivered_count(n):
    query = "SELECT Name, Status__c, Sale_Value__c, DeliveryDate__c FROM Order__c WHERE RecordTypeId = '01209000000xizgAAA'"
    orders = sf.query_all(query)
    orders = pd.DataFrame(orders['records']).drop(columns='attributes')
    todays_delivered_orders = is_today(orders, 'DeliveryDate__c')
    delivered_orders_number = todays_delivered_orders.Name.count()
    return delivered_orders_number

@app.callback(Output('delivered_orders_gmv', 'children'),
              Input('interval-component', 'n_intervals'))

def update_delivered_GMV(n):
    query = "SELECT Name, Status__c, Sale_Value__c, DeliveryDate__c FROM Order__c WHERE RecordTypeId = '01209000000xizgAAA'"
    orders = sf.query_all(query)
    orders = pd.DataFrame(orders['records']).drop(columns='attributes')
    todays_delivered_orders = is_today(orders, 'DeliveryDate__c')
    delivered_orders_GMV = round(todays_delivered_orders.Sale_Value__c.sum()/1000,1)
    delivered_orders_GMV = 'EUR ' + str(delivered_orders_GMV) + 'k'
    return delivered_orders_GMV

@app.callback(Output('invoiced_orders', 'children'),
              Input('interval-component', 'n_intervals'))

def update_invoiced(n):
    query = "SELECT Name, Status__c, Sale_Value__c, Invoice_date__c FROM Order__c WHERE RecordTypeId = '01209000000xizgAAA'"
    orders = sf.query_all(query)
    orders = pd.DataFrame(orders['records']).drop(columns='attributes')
    todays_invoiced_orders = is_today(orders, 'Invoice_date__c')
    invoiced_orders_number = todays_invoiced_orders.Name.count()
    return invoiced_orders_number

@app.callback(Output('invoiced_orders_gmv', 'children'),
              Input('interval-component', 'n_intervals'))

def update_invoiced_gmv(n):
    query = "SELECT Name, Status__c, Sale_Value__c, Invoice_date__c FROM Order__c WHERE RecordTypeId = '01209000000xizgAAA'"
    orders = sf.query_all(query)
    orders = pd.DataFrame(orders['records']).drop(columns='attributes')
    todays_invoiced_orders = is_today(orders, 'Invoice_date__c')
    invoiced_orders_GMV = round(todays_invoiced_orders.Sale_Value__c.sum()/1000,1)
    invoiced_orders_GMV_str = 'EUR ' + str(invoiced_orders_GMV) + 'k'
    return invoiced_orders_GMV_str

@app.callback(Output('completed_orders', 'children'),
              Input('interval-component', 'n_intervals'))

def update_completed(n):
    query = "SELECT Name, Completed_date__c FROM Order__c WHERE Status__c = 'completed' AND RecordTypeId = '01209000000xizgAAA'"
    orders = sf.query_all(query)
    orders = pd.DataFrame(orders['records']).drop(columns='attributes')
    todays_completed_orders = is_today(orders, 'Completed_date__c')
    completed_orders_number = todays_completed_orders.Name.count()
    return completed_orders_number

@app.callback(Output('completed_orders_gmv', 'children'),
              Input('interval-component', 'n_intervals'))

def update_completed_gmv(n):
    query = "SELECT Name, Sale_Value__c, Completed_date__c FROM Order__c WHERE Status__c = 'completed' AND RecordTypeId = '01209000000xizgAAA'"
    orders = sf.query_all(query)
    orders = pd.DataFrame(orders['records']).drop(columns='attributes')
    todays_completed_orders = is_today(orders, 'Completed_date__c')
    completed_orders_GMV = round(todays_completed_orders.Sale_Value__c.sum()/1000,1)
    completed_orders_GMV_str = 'EUR ' + str(completed_orders_GMV) + 'k'
    return completed_orders_GMV_str

if __name__ == '__main__':
    app.run_server()