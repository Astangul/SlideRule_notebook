import pandas as pd
import numpy as np
import plotly.graph_objects as go
import ipywidgets as widgets
from IPython.display import display
from ipywidgets import Output

def create_filter_plot(data):
    # Calcul des incertitudes absolues
    data["Absolute Uncertainty"] = (data["1s uncertainty"]) * data["Dose (Gy)"]

    # Ajouter une colonne pour la combinaison de filtres
    data['Filter Combo'] = data.apply(lambda row: f"{row['Particle']}_{row['Screen']}_{row['Code']}_{row['Case']}_{row['Thickness (cm)']}", axis=1)

    output = Output()  # Créez une zone d'affichage pour la figure

    # Initialiser une figure vide dans l'objet Output
    fig = go.Figure()
    fig.update_layout(
        title="Dose vs. Distances",
        xaxis_title="Distance (m) [Log]",
        yaxis_title="Dose (Gy) [Log]",
        legend_title="",
        xaxis={'type': 'log'},
        yaxis={'type': 'log', 'tickformat': '.2e'},
        showlegend=True  # Assure que la légende est toujours affichée
    )

    display(output)  # Affiche l'objet Output une seule fois

    # Fonction pour mettre à jour le graphique
    def plot_filters(particle_types, screen_types, code_types, case_types, thickness_types):
        fig.data = []  # Efface les données précédentes de la figure
        filtered_data = data[data['Particle'].isin(particle_types) & 
                             data['Screen'].isin(screen_types) &
                             data['Code'].isin(code_types) &
                             data['Case'].isin(case_types) &
                             data['Thickness (cm)'].isin(thickness_types)]

        for combo in filtered_data['Filter Combo'].unique():
            df_subset = filtered_data[filtered_data['Filter Combo'] == combo]
            fig.add_trace(go.Scatter(x=df_subset["Distance (m)"], y=df_subset["Dose (Gy)"],
                                     mode='lines+markers', name=combo,
                                     line=dict(dash='dash'),
                                     error_y=dict(type='data', array=2*df_subset["Absolute Uncertainty"],
                                                  visible=True)))
        with output:
            output.clear_output(wait=True)  # Efface la sortie précédente
            display(fig)  # Affichez la figure mise à jour

    # Création des widgets
    particle_selector = widgets.SelectMultiple(
        options=list(data['Particle'].unique()),
        value=[data['Particle'].unique()[0]],
        description='Particle:',
    )

    screen_selector = widgets.SelectMultiple(
        options=list(data['Screen'].unique()),
        value=[data['Screen'].unique()[0]],
        description='Screen:',
    )

    code_selector = widgets.SelectMultiple(
        options=list(data['Code'].unique()),
        value=[data['Code'].unique()[0]],
        description='Code:',
    )

    case_selector = widgets.SelectMultiple(
        options=list(data['Case'].unique()),
        value=[data['Case'].unique()[0]],
        description='Case:',
    )

    thickness_options = sorted(data['Thickness (cm)'].unique())
    thickness_selector = widgets.SelectMultiple(
        options=thickness_options,
        value=[thickness_options[0]],
        description='Thickness:',
    )

    interactive_plot = widgets.interactive_output(plot_filters, {
        'particle_types': particle_selector, 
        'screen_types': screen_selector, 
        'code_types': code_selector,
        'case_types': case_selector,
        'thickness_types': thickness_selector
    })

    widget_box = widgets.VBox([
        particle_selector,
        screen_selector,
        code_selector,
        case_selector,
        thickness_selector
    ])

    display(widget_box)

def plot_ratio_by_configurations(data, particles, screens, cases, codes, thicknesses):
    if not thicknesses:  # Vérifier si thicknesses est une liste vide
        thicknesses = data['Thickness (cm)'].unique().tolist()
        thicknesses.sort()  
    fig = go.Figure()

    # Configuration des titres des axes
    x_title = 'Distance (m)'
    y_title = 'Dose Ratio'

    # Boucles pour tracer les données
    for particle in particles:
        for screen in screens:
            for case in cases:
                for code in codes:
                    for thickness in thicknesses:
                        data_screen = data[(data['Screen'] == screen) &
                                           (data['Particle'] == particle) &
                                           (data['Case'] == case) &
                                           (data['Code'] == code) &
                                           (data['Thickness (cm)'] == thickness)]
                        data_no_screen = data[(data['Screen'] == 'None') &
                                              (data['Particle'] == particle) &
                                              (data['Case'] == case) &
                                              (data['Code'] == code)]

                        data_screen = data_screen.sort_values(by='Distance (m)')
                        data_no_screen = data_no_screen.sort_values(by='Distance (m)')

                        data_combined = pd.merge(data_screen, data_no_screen, on='Distance (m)', suffixes=('_screen', '_none'))
                        data_combined['Dose Ratio'] = data_combined['Dose (Gy)_screen'] / data_combined['Dose (Gy)_none']
                        data_combined['Combined Uncertainty'] = np.sqrt( data_combined['1s uncertainty_screen']**2 + data_combined['1s uncertainty_none']**2 ) * data_combined['Dose Ratio']
                        data_combined['Unique Key'] = data_combined.apply(
                            lambda x: f"{case} - {code} - {screen} - {x['Thickness (cm)_screen']}cm - {particle}", axis=1)

                        for key, group in data_combined.groupby('Unique Key'):
                            fig.add_trace(go.Scatter(
                                x=group['Distance (m)'],
                                y=group['Dose Ratio'],
                                mode='lines+markers',
                                name=key,
                                error_y=dict(type='data', array= 2 * group['Combined Uncertainty'], visible=True)
                            ))

    # Configuration des boutons pour les échelles des axes
    buttons = [
        {'method': 'relayout', 'label': 'Log X, Lin Y', 'args': [{'xaxis': {'type': 'log', 'title': x_title}, 'yaxis': {'type': 'linear', 'title': y_title}}]},
        {'method': 'relayout', 'label': 'Lin X, Lin Y', 'args': [{'xaxis': {'type': 'linear', 'title': x_title}, 'yaxis': {'type': 'linear', 'title': y_title}}]},
        {'method': 'relayout', 'label': 'Log X, Log Y', 'args': [{'xaxis': {'type': 'log', 'title': x_title}, 'yaxis': {'type': 'log', 'title': y_title}}]},
        {'method': 'relayout', 'label': 'Lin X, Log Y', 'args': [{'xaxis': {'type': 'linear', 'title': x_title}, 'yaxis': {'type': 'log', 'title': y_title}}]}
    ]

    # Mise à jour du layout avec les boutons et échelles par défaut "Log X, Lin Y"
    fig.update_layout(
        title='Ratio of Prompt Dose with Screen to No Screen by Configuration',
        xaxis={'type': 'log', 'title': x_title},
        yaxis={'type': 'linear', 'title': y_title},
        updatemenus=[{
            'buttons': buttons,
            'direction': 'down',
            'showactive': True,
            'x': 1.0,  # positionnement au centre sur l'axe horizontal
            'xanchor': 'right',
            'y': 1.15,  # positionnement au-dessus du graphique
            'yanchor': 'top'
        }]
    )

    # Affichage du graphique
    fig.show()

def plot_categorical_bar_chart(data, particles, screens, cases, codes, thicknesses):
    if thicknesses is None or len(thicknesses) == 0:  # Vérifier si thicknesses est None ou une liste vide
        thicknesses = data['Thickness (cm)'].unique().tolist()
        thicknesses.sort()
    fig = go.Figure()

    # Configuration des axes
    x_title = 'Distance (m)'
    y_title = 'Dose Ratio'

    # Obtenir les distances uniques comme chaînes de caractères
    unique_distances = sorted(data['Distance (m)'].unique())
    distance_labels = [str(dist) for dist in unique_distances]

    # Créer des séries pour chaque combinaison unique
    for particle in particles:
        for screen in screens:
            for case in cases:
                for code in codes:
                    for thickness in thicknesses:
                        # Créer une clé unique pour chaque configuration
                        unique_key = f"{case} - {code} - {screen} - {thickness}cm - {particle}"

                        # Filtrer les données pour la configuration donnée
                        data_screen = data[
                            (data['Screen'] == screen) & 
                            (data['Thickness (cm)'] == thickness) &
                            (data['Particle'] == particle) & 
                            (data['Case'] == case) & 
                            (data['Code'] == code)
                        ]
                        
                        data_no_screen = data[
                            (data['Screen'] == 'None') & 
                            (data['Particle'] == particle) & 
                            (data['Case'] == case) & 
                            (data['Code'] == code)
                        ]

                        # Trier par distance
                        data_screen = data_screen.sort_values(by='Distance (m)')

                        # Combiner les données pour calculer le ratio de dose
                        data_combined = pd.merge(
                            data_screen,
                            data_no_screen,
                            on='Distance (m)',
                            suffixes=('_screen', '_none')
                        )

                        # Calcul du ratio de dose
                        data_combined['Dose Ratio'] = data_combined['Dose (Gy)_screen'] / data_combined['Dose (Gy)_none']
                        data_combined['Combined Uncertainty'] = data_combined['Dose Ratio'] * np.sqrt(
                            data_combined['1s uncertainty_screen']**2 + 
                            data_combined['1s uncertainty_none']**2
                        )

                        # Créer des barres pour chaque distance unique
                        bar_data = []

                        for distance in unique_distances:
                            subset = data_combined[data_combined['Distance (m)'] == distance]
                            if not subset.empty:
                                x_values = [str(distance)] * len(subset)  # Répéter la distance pour chaque point de données
                                y_values = subset['Dose Ratio'].tolist()  # Liste des valeurs de ratio de dose
                                uncertainties = subset['Combined Uncertainty'].tolist()  # Liste des incertitudes combinées
                                for x, y, uncertainty in zip(x_values, y_values, uncertainties):
                                    bar_data.append({
                                        'x': [x],
                                        'y': [y],
                                        'error_y': {
                                            'type': 'data',
                                            'array': [2 * uncertainty],
                                            'visible': True
                                        },
                                        'name': unique_key  # Utilisation de la clé unique comme nom de la série
                                    })
                        # Ajout des barres pour cette configuration unique
                        if bar_data:
                            fig.add_trace(
                                go.Bar(
                                    x=[item['x'][0] for item in bar_data],
                                    y=[item['y'][0] for item in bar_data],
                                    name=bar_data[0]['name'],
                                    error_y={
                                        'type': 'data',
                                        'array': [item['error_y']['array'][0] for item in bar_data],
                                        'visible': True,
                                        'thickness': 1,
                                    }
                                )
                            )

    # Configuration du layout
    fig.update_layout(
        title='Ratio of Prompt Dose with Screen to No Screen [Bar Chart]',
        xaxis=dict(
            title=x_title,
            tickvals=distance_labels,  # Utilisation des distances comme valeurs catégoriques
            ticktext=distance_labels  # Texte des tickvals
        ),
        yaxis=dict(
            title=y_title
        ),
        barmode='group'  # Pour que les barres soient groupées
    )

    # Affichage du graphique
    fig.show()
