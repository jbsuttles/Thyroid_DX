import dash_table
from flask import Flask, request, render_template, redirect, url_for, session, g

import dash
import dash_core_components as dcc
import dash_html_components as html
from sqlalchemy import create_engine
import psycopg2
import plotly.express as px
import pandas as pd

import os
import pickle
import numpy as np

# Initialize Flask
server = Flask(__name__)

server.secret_key = os.urandom(24)

# Load ML model
clf_model = pickle.load(open("clf_model.pkl", "rb"))

# Initialize Dash
app = dash.Dash(__name__, server=server, url_base_pathname='/dashboard/')


@server.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        session.pop('user', None)

        if request.form['password'] == 'admin' and request.form['username'] == 'admin':
            session['user'] = request.form['username']
            return redirect(url_for('main'))

    return render_template('index.html')


@server.route('/main')
def main():
    if g.user:
        return render_template('main.html', user=session['user'])
    return redirect(url_for('index'))


@server.route('/main', methods=['POST'])
def getresults():
    if request.method == 'POST':
        # Initialize patient_dx to -1 when page is loaded
        patient_dx = -1

        age = float(request.form['age'])
        sex = float(request.form['sex'])
        thyroxine = float(request.form['thyroxine'])
        antithyroid = float(request.form['antithyroid'])
        thyroid_surgery = float(request.form['thyroid_surgery'])
        pregnant = float(request.form['pregnant'])
        sick = float(request.form['sick'])
        tumor = float(request.form['tumor'])
        lithium = float(request.form['lithium'])
        goitre = float(request.form['goitre'])
        tsh_measured = float(request.form['tsh_measured'])
        t3_measured = float(request.form['t3_measured'])
        tt4_measured = float(request.form['tt4_measured'])
        t4u_measured = float(request.form['t4u_measured'])
        fti_measured = float(request.form['fti_measured'])

        """
        The following section will set tsh, t3. tt4. t4u. fti with the HTML input unless
        the associated measured result was 'No'. If the associated measured result is 'No',
        the average of the column from the model is used.
        """
        if tsh_measured == 0:
            tsh = 5.923180
        else:
            tsh = float(request.form['tsh'])

        if t3_measured == 0:
            t3 = 1.939749
        else:
            t3 = float(request.form['t3'])

        if tt4_measured == 0:
            tt4 = 108.850000
        else:
            tt4 = float(request.form['tt4'])

        if t4u_measured == 0:
            t4u = 0.978199
        else:
            t4u = float(request.form['t4u'])

        if fti_measured == 0:
            fti = 115.397771
        else:
            fti = float(request.form['fti'])

        '''
        Combine values into a list in the same order the model expects
        '''
        patient_result = [age, tsh, t3, tt4, t4u, fti, sex, thyroxine, antithyroid,
                          thyroid_surgery, pregnant, sick, tumor, lithium, goitre,
                          tsh_measured, t3_measured, tt4_measured, t4u_measured, fti_measured]
        print(patient_result)
        patient_array = np.array(patient_result)
        patient_reshape = patient_array.reshape(1, -1)
        patient_dx = clf_model.predict_proba(patient_reshape)
        print(patient_dx)
        return render_template('results.html', patient_dx=patient_dx)


@server.route('/results')
def results():
    if g.user:
        return render_template('results.html', user=session['user'])
    return redirect(url_for('index'))


@server.before_request
def before_request():
    g.user = None

    if 'user' in session:
        g.user = session['user']


@server.route('/dropsession')
def dropsession():
    session.pop('user', None)
    return render_template('index.html')


# Create a instance to PostSQL DB


# Postgres username, password, and database name
POSTGRES_ADDRESS = 'localhost'
POSTGRES_PORT = '5432'
POSTGRES_USERNAME = 'postgres'
POSTGRES_PASSWORD = 'Sparky89!'
POSTGRES_DBNAME = 'C964'
# A long string that contains the necessary Postgres login information
postgres_str = ('postgresql://{username}:{password}@{ipaddress}:{port}/{dbname}'
                .format(username=POSTGRES_USERNAME,
                        password=POSTGRES_PASSWORD,
                        ipaddress=POSTGRES_ADDRESS,
                        port=POSTGRES_PORT,
                        dbname=POSTGRES_DBNAME))
# Create the connection
cnx = create_engine(postgres_str)

# Create variables for scatter plot graph
tsh = pd.read_sql_query('''select dx, age, tsh from thyroid where age <> '?' and tsh <> '?' ''', cnx)

# Create scatter plot graph
fig_sp = px.scatter(tsh, x='age', y='tsh', color='dx',
                    labels={
                        'age': 'Age',
                        'tsh': 'TSH',
                        'dx': 'Diagnosis'
                    }
                    )
fig_sp.update_layout(
    title={
        'text': '<b>Age and TSH levels Relationship</b>',
        'x': 0.5,
        'xanchor': 'center',
        'yanchor': 'top'
    }
)

# Create variables for bar graph
preg_neg = pd.read_sql_query('''select count(pregnant) from thyroid where pregnant='t' and sex <> '?' and dx 
                              ='negative';''', cnx)

preg_ht = pd.read_sql_query('''select count(pregnant) from thyroid where pregnant='t' and sex <> '?' and dx 
                            ='hypothyroid';''', cnx)

surg_neg = pd.read_sql_query('''select count(thyroid_surgery) from thyroid where thyroid_surgery='t' and 
                             sex <> '?' and dx ='negative';''', cnx)

surg_ht = pd.read_sql_query('''select count(thyroid_surgery) from thyroid where thyroid_surgery='t' and sex <> '?' 
                            and dx ='hypothyroid';''', cnx)

sick_neg = pd.read_sql_query('''select count(sick) from thyroid where sick='t' and sex <> '?' 
                             and dx ='negative';''', cnx)

sick_ht = pd.read_sql_query('''select count(sick) from thyroid where sick='t' and sex <> '?' 
                            and dx ='hypothyroid';''', cnx)

tumor_neg = pd.read_sql_query('''select count(tumor) from thyroid where tumor='t' and sex <> '?' 
                              and dx ='negative';''', cnx)

tumor_ht = pd.read_sql_query('''select count(tumor) from thyroid where tumor='t' and sex <> '?' 
                             and dx ='hypothyroid';''', cnx)

lithium_neg = pd.read_sql_query('''select count(lithium) from thyroid where lithium='t' and sex <> '?' 
                                and dx ='negative';''', cnx)

lithium_ht = pd.read_sql_query('''select count(lithium) from thyroid where lithium='t' and sex <> '?' 
                               and dx ='hypothyroid';''', cnx)

goitre_neg = pd.read_sql_query('''select count(goitre) from thyroid where goitre='t' and sex <> '?' 
                               and dx ='negative';''', cnx)

goitre_ht = pd.read_sql_query('''select count(goitre) from thyroid where goitre='t' and sex <> '?' 
                              and dx ='hypothyroid';''', cnx)

# Create bar graph
bar_graph = pd.DataFrame({
    "Patient Medical History": ['Pregnant', 'Thyroid Surgery', 'Sick', 'Tumor', 'Lithium', 'Goitre',
                                'Pregnant', 'Thyroid Surgery', 'Sick', 'Tumor', 'Lithium', 'Goitre'],
    "# of Occurrences": [preg_neg.iloc[0]['count'], surg_neg.iloc[0]['count'], sick_neg.iloc[0]['count'],
                         tumor_neg.iloc[0]['count'], lithium_neg.iloc[0]['count'], goitre_neg.iloc[0]['count'],
                         preg_ht.iloc[0]['count'], surg_ht.iloc[0]['count'], sick_ht.iloc[0]['count'],
                         tumor_ht.iloc[0]['count'], lithium_ht.iloc[0]['count'], goitre_ht.iloc[0]['count']],
    "Diagnosis": ['Negative', 'Negative', 'Negative', 'Negative', 'Negative', 'Negative',
                  'Hypothyroid', 'Hypothyroid', 'Hypothyroid', 'Hypothyroid', 'Hypothyroid', 'Hypothyroid']
})

fig_bg = px.bar(bar_graph, x="Patient Medical History", y="# of Occurrences", color="Diagnosis", barmode="group")

fig_bg.update_layout(
    title={
        'text': '<b>Occurrences of Patient Medical History</b>',
        'x': 0.5,
        'xanchor': 'center',
        'yanchor': 'top'
    }
)

# Create variable for pie graph
tsh_pg = pd.read_sql_query('''select count(tsh_measured) from thyroid where dx = 'hypothyroid' and sex <> '?' 
                           and tsh_measured = 'y';''', cnx)

t3_pg = pd.read_sql_query('''select count(t3_measured) from thyroid where dx = 'hypothyroid' and sex <> '?' 
                          and t3_measured = 'y';''', cnx)

tt4_pg = pd.read_sql_query('''select count(tt4_measured) from thyroid where dx = 'hypothyroid' and sex <> '?' 
                           and tt4_measured = 'y';''', cnx)

t4u_pg = pd.read_sql_query('''select count(t4u_measured) from thyroid where dx = 'hypothyroid' and sex <> '?' 
                           and t4u_measured = 'y';''', cnx)

fti_pg = pd.read_sql_query('''select count(fti_measured) from thyroid where dx = 'hypothyroid' and sex <> '?' 
                           and fti_measured = 'y';''', cnx)

# Create pie graph
pie_graph = pd.DataFrame({
    "Laboratory Tests": ['TSH', 'T3', 'Total T4', 'Free T4', 'Free Thyroxine Index'],
    "# of Orders": [tsh_pg.iloc[0]['count'], t3_pg.iloc[0]['count'], tt4_pg.iloc[0]['count'], t4u_pg.iloc[0]['count'],
                    fti_pg.iloc[0]['count']]
})

fig_pg = px.pie(pie_graph, values="# of Orders", names="Laboratory Tests")

fig_pg.update_layout(
    title={
        'text': '<b># of Laboratory Test Used for Thyroid Diagnosis</b>',
        'x': 0.5,
        'xanchor': 'center',
        'yanchor': 'top'
    }
)

# Create variable for raw dataset
thyroid_table = pd.read_sql_query('''select dx, age, sex, on_thyroxine, on_antithyroid_medication, thyroid_surgery, 
pregnant, sick, tumor, lithium, goitre, tsh_measured, tsh, t3_measured, t3, tt4_measured,
tt4, t4u_measured, t4u, fti_measured, fti from thyroid;''', cnx)

# Create app layout
app.layout = html.Div([
    html.Div(className="main", children=[
        html.Div(className="menu",
                 children=[
                     html.Ul(children=[
                         html.Li(html.A("Main", href='/main')),
                         html.Li(html.A("Data Visualization and Dataset", href='/dashboard/', className='active'))
                     ]
                     )
                 ]),
        html.Div(className="main-screen",
                 children=[
                     html.H1(children='Data Visualization and Dataset',
                             className="title"),
                     dcc.Graph(
                         id='age-tsh',
                         figure=fig_sp,
                     ),
                     dcc.Graph(
                         id="bar_graph",
                         figure=fig_bg
                     ),
                     dcc.Graph(
                         id="pie_graph",
                         figure=fig_pg
                     )
                     ,
                     html.H3(children='Raw Dataset Used for Thyroid Diagnosis ML Model',
                             className="title"),
                     dash_table.DataTable(
                         id='table',
                         columns=[{"name": i, "id": i} for i in thyroid_table.columns],
                         data=thyroid_table.to_dict('records'),
                         page_size=20,
                         style_table={'overflow': 'scroll'},
                         style_data_conditional=[
                             {
                                 'if': {'row_index': 'odd'},
                                 'backgroundColor': 'rgb(248, 248, 248)'
                             }
                         ],
                         style_header={
                             'backgroundColor': 'rgb(230, 230, 230)',
                             'fontWeight': 'bold'
                         }
                     )
                 ],
                 ),
    ]),
]
)

if __name__ == "__main__":
    server.run(debug=True)
