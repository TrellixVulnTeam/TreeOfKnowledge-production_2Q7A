from collection.models import Simulation_model, Rule, Likelihood_fuction, Attribute, Rule_parameter
import json
import pandas as pd
import numpy as np
from collection.functions import query_datapoints, get_from_db
import elfi
from operator import itemgetter
import random
import random
from scipy.stats import rv_histogram
import matplotlib.pyplot as plt
import seaborn as sns
import math
from copy import deepcopy
from colour import Color
import re

# called from edit_model.html
class Simulator:
    """This class gets initialized with values specified in edit_simulation.html.
    This includes the initial values for some objects. 
    By running the simulation the values for the next timesteps are determined and 
    if possible compared to the values in the KB."""


    objects_dict = {}
    simulation_start_time = 946684800
    simulation_end_time = 1577836800
    timestep_size = 31622400

    y0_columns = []
    y0_column_dt = {}
    parameter_columns = []
    rules = []
    rule_priors = []
    posterior_values_to_delete = {}
    posterior_values = {}
    number_of_batches = 0
    currently_running_learn_likelihoods = False



# =================================================================================================================
#   _____       _ _   _       _ _         
#  |_   _|     (_) | (_)     | (_)        
#    | |  _ __  _| |_ _  __ _| |_ _______ 
#    | | | '_ \| | __| |/ _` | | |_  / _ \
#   _| |_| | | | | |_| | (_| | | |/ /  __/
#  |_____|_| |_|_|\__|_|\__,_|_|_/___\___|
# 
# =================================================================================================================

    def __init__(self, simulation_id):

        self.simulation_id = simulation_id
        simulation_model_record = Simulation_model.objects.get(id=simulation_id)

        # self.elfi_model = elfi.ElfiModel() 
        elfi.new_model()
        self.objects_dict = json.loads(simulation_model_record.objects_dict)
        self.simulation_start_time = simulation_model_record.simulation_start_time
        self.simulation_end_time = simulation_model_record.simulation_end_time
        self.timestep_size = simulation_model_record.timestep_size  
        self.is_timeseries_analysis = simulation_model_record.is_timeseries_analysis
        self.rule_priors = [] 


        # logging
        self.progress_tracking_file_name = 'collection/static/webservice files/runtime_data/simulation_progress_' + str(self.simulation_id) + '.txt'
        with open(self.progress_tracking_file_name, "w") as progress_tracking_file:
            progress_tracking_file.write(json.dumps({"learning_likelihoods": True, "nb_of_accepted_simulations": "", "nb_of_accepted_simulations_current": "" , "learning__post_processing": "Initializing: retrieving validation data from the knowledge base."  , "running_monte_carlo": True, "monte_carlo__simulation_number": "", "monte_carlo__number_of_simulations":  "", "monte_carlo__post_processing":"Initializing: retrieving validation data from the knowledge base."}))



        # #(simulations)
        self.nb_of_accepted_simulations = 500
        self.elfi_sampler = None


        #  --- colors ---
        # green = Color("#97CF99")
        # color_objects = list(green.range_to(Color("#D1A19C"),1001))
        # self.colors = [color.hex for color in color_objects]
        # colour = self.colors[int(min(error,1.)*1000)]


        #  --- df ---
        self.df = query_datapoints.get_data_from_related_objects(self.objects_dict, self.simulation_start_time, self.simulation_end_time,)
        self.df.fillna(value=pd.np.nan, inplace=True)
        self.df.index = range(len(self.df))


        #  --- y0_columns & y0_column_dt ---
        y_value_attributes = json.loads(simulation_model_record.y_value_attributes)
        for y_value_attribute in y_value_attributes:
            column_name = 'obj' + str(y_value_attribute['object_number']) + 'attr' + str(y_value_attribute['attribute_id'])
            self.y0_columns.append(column_name)
            self.y0_column_dt[column_name] = Attribute.objects.get(id=y_value_attribute['attribute_id']).data_type



        #  --- df and y0_values ---
        self.y0_values = []
        if self.is_timeseries_analysis:
            
            times = np.arange(self.simulation_start_time, self.simulation_end_time, self.timestep_size)
            merged_object_data_tables = query_datapoints.get_data_from_related_objects__multiple_timesteps(self.objects_dict, times, self.timestep_size)
            # print('-------merged_object_data_tables1--------')
            # print(merged_object_data_tables.head())
            # print(merged_object_data_tables.columns)
            merging_columns =  ['obj' + obj_num + 'attrobject_id' for obj_num in self.objects_dict.keys()]
            # print('===============================================')
            # print(merging_columns)
            # print('<><><><><><>')
            # print(self.df.head())
            # print('<><><><><><>')
            # print(self.df[merging_columns].head())
            # print('<><><><><><>')
            # print(merged_object_data_tables[merging_columns].head())
            # print('===============================================')
            merged_periods_df = pd.merge(self.df, merged_object_data_tables, on=merging_columns, how='outer', suffixes=['','__from_periods'])
            original_df_columns = self.df.columns

            for col in self.y0_columns:
                desired_column_names = [col + 'period'+ str(period) for period in range(len(times)-1)]
                for desired_column_name in desired_column_names:
                    if desired_column_name not in merged_periods_df.columns:
                        merged_periods_df[desired_column_name] = np.nan

            merged_periods_df = self.reduce_number_of_rows(merged_periods_df, 500)
            merged_periods_df.index = range(len(merged_periods_df))

            self.df = merged_periods_df[original_df_columns]
            merged_periods_df = merged_periods_df[[col for col in merged_periods_df.columns if col.split('period')[0] in self.y0_columns]]
            # print('=== Testing  ==================================================')
            # merged_periods_df.to_csv('C:/Users/l412/Documents/2 temporary stuff/2020-01-20/merged_periods_df__timeseries_analysis.csv', index=False)
            # print('===============================================================')
            self.y0_values = [row for index, row in sorted(merged_periods_df.to_dict('index').items())]

        else:
            self.df = self.reduce_number_of_rows(self.df, 500)
            df_copy = pd.DataFrame(self.df[self.y0_columns].copy())
            df_copy.columns = [col + 'period0' for col in df_copy.columns]
            df_copy = df_copy[[col for col in df_copy.columns if col.split('period')[0] in self.y0_columns]]
            # print('=== Testing  ==================================================')
            # df_copy.to_csv('C:/Users/l412/Documents/2 temporary stuff/2020-01-20/df_copy_crosssectional_analysis.csv', index=False)
            # print('===============================================================')
            self.y0_values = [row for index, row in sorted(df_copy.to_dict('index').items())]

        self.y0_values_df = pd.DataFrame(self.y0_values)
        # print('=== Testing  ==================================================')
        # self.y0_values_df.to_csv('C:/Users/l412/Documents/2 temporary stuff/2020-02-06/y0_values_df.csv', index=False)
        # print('===============================================================')




        #  --- Rules ---

        # preparation: put relations into a dictionary for easier access
        relation_dict = {}
        object_numbers = self.objects_dict.keys()
        for object_number in object_numbers:
            relation_dict[object_number] = {}
            for relation in self.objects_dict[str(object_number)]['object_relations']:
                if relation['attribute_id'] not in relation_dict[object_number]:
                    relation_dict[object_number][relation['attribute_id']] = [relation['target_object_number']]
                else:
                    relation_dict[object_number][relation['attribute_id']] += [relation['target_object_number']]
        print('------------ relation_dict ------------')
        print(relation_dict)

        # adapt condition_exec and effect_exec to current df
        number_of_priors = 0  
        for object_number in object_numbers:

            attribute_ids = self.objects_dict[str(object_number)]['object_rules'].keys()
            print('attribute_ids: ' + str(attribute_ids))
            for attribute_id in attribute_ids:

                rule_ids = self.objects_dict[str(object_number)]['object_rules'][str(attribute_id)]['execution_order']
                # print('rule_ids: ' + str(rule_ids))
                for rule_id in set(rule_ids):
                    print('object_number: ' + str(object_number) + '; attribute_id: ' + str(attribute_id) + '; rule_id: ' + str(rule_id) + '; ')
                    rule = self.objects_dict[str(object_number)]['object_rules'][str(attribute_id)]['used_rules'][str(rule_id)]
                    print('1')
                    # if set(rule['used_attribute_ids']) <= set(self.df.columns): # the attributes used in this rule must appear in df
                    

                    if self.is_timeseries_analysis or 'df.delta_t' not in rule['effect_exec']:  # don't include rules containing delta_t for cross-sectional analyses 

                        if rule['effect_is_calculation']:
                            rule['effect_exec'] = rule['effect_exec'].replace('df.attr', 'df.obj' + str(object_number) + 'attr')
                        elif rule['changed_var_data_type'] in ['relation','int']:
                            rule['effect_exec'] = int(rule['effect_exec'])
                        elif rule['changed_var_data_type'] == 'real':
                            rule['effect_exec'] = float(rule['effect_exec'])
                        elif rule['changed_var_data_type'] == 'boolean':
                            rule['effect_exec'] = (rule['effect_exec'] in ['True','true','T','t'])
                        
                        # --- convert condition_exec ---
                        if not rule['is_conditionless']:

                            # exists_expressions
                            exists_expressions = re.findall(r'\([∀∃]rel\d+\)\[[^\]]*\]', rule['condition_exec'])
                            for exists_expression in exists_expressions:
                                relation_id = int(re.findall(r'\d+', exists_expression)[0])
                                target_object_numbers = relation_dict[object_number][relation_id]

                                exists_expression_inner = re.findall(r'\[.*\]',exists_expression)[0]
                                list_of_different_inner_expressions = [exists_expression_inner.replace('df.rel' + str(relation_id), 'df.obj'+ str(target_object_number)) for target_object_number in target_object_numbers]
                                if exists_expression[1]=='∃':
                                    replacement = '(' + ' or '.join(list_of_different_inner_expressions) + ')'
                                else:
                                    replacement = '(' + ' and '.join(list_of_different_inner_expressions) + ')'
                                
                                rule['condition_exec'] = rule['condition_exec'].replace(exists_expression, replacement)


                            # relations
                            # first level
                            relation_occurences = re.findall(r'df.rel\d+\.', rule['condition_exec'])
                            for relation_occurence in relation_occurences:
                               relation_id = int(re.findall(r'\d+', relation_occurence)[0]) 
                               print('relation_dict[' + str(object_number) + '][' + str(relation_id) + '][0]')
                               target_object_number = relation_dict[object_number][relation_id][0]
                               rule['condition_exec'] = rule['condition_exec'].replace(relation_occurence, 'df.obj' + str(target_object_number))

                            # further levels
                            for level in range(2): # you can maximally have a relation of a relation of a relation (=3)
                                relation_occurences = re.findall(r'df.obj\d+rel\d+\.', rule['condition_exec'])
                                for relation_occurence in relation_occurences:
                                    given_object_number = int(re.findall(r'\d+', relation_occurence)[0]) 
                                    relation_id = int(re.findall(r'\d+', relation_occurence)[1]) 
                                    target_object_number = relation_dict[given_object_number][relation_id][0]
                                    rule['condition_exec'] = rule['condition_exec'].replace(relation_occurence, 'df.obj' + str(target_object_number))


                        rule['condition_exec'] = rule['condition_exec'].replace('df.attr', 'df.obj' + str(object_number) + 'attr')
                        rule['column_to_change'] = 'obj' + str(object_number) + 'attr' + str(rule['changed_var_attribute_id'])
                        rule['object_number'] = object_number

                        rule['parameters'] = {}
                        for used_parameter_id in rule['used_parameter_ids']:
                            parameter = Rule_parameter.objects.get(id=used_parameter_id)
                            rule['parameters'][used_parameter_id] = {'min_value': parameter.min_value, 'max_value': parameter.max_value}


                        # ---  priors  ---
                        if rule['learn_posterior']:
                            # rule probability
                            if not rule['has_probability_1']:
                                new_prior = elfi.Prior('uniform', 0, 1, name='prior__object' + str(object_number) + '_rule' + str(rule_id))  
                                print('adding prior ' + str(number_of_priors) + ': prior__object' + str(object_number) + '_rule' + str(rule_id))
                                self.rule_priors.append(new_prior)
                                rule['prior_index'] = number_of_priors
                                number_of_priors += 1

                            # parameter
                            for used_parameter_id in rule['used_parameter_ids']:
                                min_value = rule['parameters'][used_parameter_id]['min_value']
                                max_value = rule['parameters'][used_parameter_id]['max_value']
                                new_prior = elfi.Prior('uniform', min_value, max_value, name='prior__object' + str(object_number) + '_rule' + str(rule_id) + '_param' + str(used_parameter_id))  
                                print('adding prior ' + str(number_of_priors) + ': prior__object' + str(object_number) + '_rule' + str(rule_id) + '_param')
                                self.rule_priors.append(new_prior)
                                rule['parameters'][used_parameter_id]['prior_index'] = number_of_priors
                                number_of_priors += 1
                                self.parameter_columns.append('param' + str(used_parameter_id))

                                self.posterior_values_to_delete['param' + str(used_parameter_id)] = []
                                self.posterior_values['param' + str(used_parameter_id)] = []


                        # ---  histograms  ---
                        # rule probability
                        if (not rule['has_probability_1']) and (not rule['learn_posterior']):
                            # if a specific posterior for this simulation has been learned, take this, else take the combined posterior of all other simulations
                            histogram, mean, standard_dev, message= get_from_db.get_single_pdf(simulation_id, object_number, rule_id, True)
                            if histogram is None:
                                histogram, mean, standard_dev = get_from_db.get_rules_pdf(rule_id, True)
                            rule['histogram'] = histogram

                        # parameter
                        if not rule['learn_posterior']:
                            for used_parameter_id in rule['used_parameter_ids']: 
                                histogram, mean, standard_dev, message= get_from_db.get_single_pdf(simulation_id, object_number, used_parameter_id, False)
                                if histogram is None:
                                    histogram, mean, standard_dev = get_from_db.get_rules_pdf(used_parameter_id, False)

                                # change to the parameter's range
                                min_value = rule['parameters'][used_parameter_id]['min_value']
                                max_value = rule['parameters'][used_parameter_id]['max_value']
                                histogram = (histogram[0], np.linspace(min_value,max_value,31))
                                rule['parameters'][used_parameter_id]['histogram'] = histogram
                                self.parameter_columns.append('param' + str(used_parameter_id))


                        # check if all the mentioned columns appear in df
                        mentioned_columns = re.findall(r'df\.[a-zA-Z0-9_]+', rule['condition_exec'] + ' ' + rule['effect_exec'] )
                        mentioned_columns = [col for col in mentioned_columns if col[:8] != 'df.param']
                        df_columns = ['df.'+col for col in self.df.columns]
                        if (set(mentioned_columns) <= set(df_columns + ['df.delta_t'])):
                            self.rules.append(rule)



        #  --- Posterior Values to Delete ---
        for rule in self.rules:
            print('||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||')
            print('rule_id: ' + str(rule['id']))
            self.posterior_values_to_delete[rule['id']] = []
            self.posterior_values[rule['id']] = []





# ==========================================================================================
#    __  __       _       
#   |  \/  |     (_)      
#   | \  / | __ _ _ _ __  
#   | |\/| |/ _` | | '_ \ 
#   | |  | | (_| | | | | |
#   |_|  |_|\__,_|_|_| |_|
# 
# ==========================================================================================

    def run(self):
        

        if len(self.rule_priors) > 0:
            self.nb_of_accepted_simulations = 500
            self.__learn_likelihoods()

        (simulation_data_df, triggered_rules_df, errors_df) = self.__run_monte_carlo_simulation(300)
        self.__post_process_data(simulation_data_df, triggered_rules_df, errors_df, 300)






    def __learn_likelihoods(self):
        print('=======  learn_likelihoods  =======')
        # PART 1 - Run the Simulation
        self.currently_running_learn_likelihoods = True
        batch_size = len(self.df)

        with open(self.progress_tracking_file_name, "w") as progress_tracking_file:
            progress_dict_string = json.dumps({"learning_likelihoods": True, "nb_of_accepted_simulations_total": self.nb_of_accepted_simulations, "nb_of_accepted_simulations_current": 0,  "learning__post_processing": "" , "running_monte_carlo": False })
            progress_tracking_file.write(progress_dict_string)

        print('learn_likelihoods1')
        Y = elfi.Simulator(self.likelihood_learning_simulator, self.df, self.rules, *self.rule_priors, observed=self.y0_values)
        # Y = elfi.Simulator(self.likelihood_learning_simulator, self.df, self.rules, *self.rule_priors, observed=self.y0_values, model=self.elfi_model)
        S1 = elfi.Summary(self.unchanged, Y)
        # S1 = elfi.Summary(self.unchanged, Y, model=self.elfi_model)
        d = elfi.Distance(self.n_dimensional_distance, S1)
        # d = elfi.Distance(self.n_dimensional_distance, S1, model=self.elfi_model)
        rej = elfi.Rejection(d, batch_size=batch_size, seed=30052017)
        # rej = elfi.Rejection(self.elfi_model, d, batch_size=batch_size, seed=30052017)
        print('learn_likelihoods2')
        self.elfi_sampler = rej
        print('learn_likelihoods3: ' + str(self.nb_of_accepted_simulations))
        result = rej.sample(self.nb_of_accepted_simulations, threshold=.5)
        self.currently_running_learn_likelihoods = False


        # PART 2 - Post Processing
        for rule_number, rule in enumerate(self.rules):

            with open(self.progress_tracking_file_name, "w") as progress_tracking_file:
                progress_tracking_file.write(json.dumps({"learning_likelihoods": True, "nb_of_accepted_simulations": self.nb_of_accepted_simulations, "nb_of_accepted_simulations_current": self.nb_of_accepted_simulations , "learning__post_processing": "Postprocessing rule " + str(rule_number) + "/" + str(len(self.rules))  , "running_monte_carlo": False }))


            # histogram
            if rule['learn_posterior']:
                if not rule['has_probability_1']:
                    print('==== post-processing rule ' + str(rule['id']) + '  ===================================================')
                    samples = result.samples['prior__object' + str(rule['object_number']) + '_rule' + str(rule['id']) ]

                    # version 1
                    histogram = np.histogram(samples, bins=30, range=(0.0,1.0))
                    histogram_of_to_be_removed = np.histogram(self.posterior_values_to_delete[rule['id']], bins=30, range=(0.0,1.0))
                    histogram = ((histogram[0] - histogram_of_to_be_removed[0]).tolist(),histogram[1].tolist())

                    # version 2
                    histogram  = np.histogram(self.posterior_values[rule['id']], bins=30, range=(0.0,1.0))
                    print('histogram: ' + str(histogram))

                    # nb_of_simulations, nb_of_sim_in_which_rule_was_used, nb_of_values_in_posterior
                    nb_of_simulations = self.number_of_batches * batch_size
                    nb_of_sim_in_which_rule_was_used = nb_of_simulations - len(self.posterior_values_to_delete[rule['id']])
                    nb_of_values_in_posterior = len(samples)

                    # PART 2.1: update the rule's histogram - the next simulation will use the newly learned probabilities
                    self.rules[rule_number]['histogram'] = histogram 

                    # PART 2.2: save the learned likelihood function to the database
                    list_of_probabilities_str = json.dumps(list( np.array(histogram[0]) * 30/ np.sum(histogram[0])))
                    print('list_of_probabilities_str: ' + list_of_probabilities_str)

                    try:
                        likelihood_fuction = Likelihood_fuction.objects.get(simulation_id=self.simulation_id, rule_id=rule['id'])
                        likelihood_fuction.list_of_probabilities = list_of_probabilities_str
                        likelihood_fuction.nb_of_simulations = nb_of_simulations
                        likelihood_fuction.nb_of_sim_in_which_rule_was_used = nb_of_sim_in_which_rule_was_used
                        likelihood_fuction.nb_of_values_in_posterior = nb_of_values_in_posterior
                        likelihood_fuction.save()
                        print('saved to existing Likelihood_fuction ' + str(likelihood_fuction.id))

                    except:
                        likelihood_fuction = Likelihood_fuction(simulation_id=self.simulation_id, 
                                                                object_number=rule['object_number'],
                                                                rule_id=rule['id'], 
                                                                list_of_probabilities=list_of_probabilities_str,
                                                                nb_of_simulations=nb_of_simulations,
                                                                nb_of_sim_in_which_rule_was_used=nb_of_sim_in_which_rule_was_used,
                                                                nb_of_values_in_posterior=nb_of_values_in_posterior)
                        likelihood_fuction.save()
                        print('saved to new Likelihood_fuction ' + str(likelihood_fuction.id))


                for used_parameter_id in rule['used_parameter_ids']:
                    print('==== post-processing parameter ' + str(used_parameter_id) + '  ===================================================')
                    samples = result.samples['prior__object' + str(rule['object_number']) + '_rule' + str(rule['id']) + '_param' + str(used_parameter_id)]

                    min_value = rule['parameters'][used_parameter_id]['min_value']
                    max_value = rule['parameters'][used_parameter_id]['max_value']

                    # version 1
                    histogram = np.histogram(samples, bins=30, range=(min_value,max_value))
                    histogram_of_to_be_removed = np.histogram(self.posterior_values_to_delete['param' + str(used_parameter_id)], bins=30, range=(min_value,max_value))
                    histogram = ((histogram[0] - histogram_of_to_be_removed[0]).tolist(),histogram[1].tolist())

                    # version 2
                    histogram = np.histogram(self.posterior_values['param' + str(used_parameter_id)], bins=30, range=(min_value,max_value))
                    print('histogram: ' + str(histogram))




                    

                    # nb_of_simulations, nb_of_sim_in_which_rule_was_used, nb_of_values_in_posterior
                    nb_of_simulations = self.number_of_batches * batch_size
                    nb_of_sim_in_which_rule_was_used = nb_of_simulations - len(self.posterior_values_to_delete['param' + str(used_parameter_id)])
                    nb_of_values_in_posterior = len(samples)

                    # PART 2.1: update the rule's histogram - the next simulation will use the newly learned probabilities
                    self.rules[rule_number]['parameters'][used_parameter_id]['histogram'] = histogram 

                    # PART 2.2: save the learned likelihood function to the database
                    list_of_probabilities_str = json.dumps(list( np.array(histogram[0]) * 30/ np.sum(histogram[0])))
                    print('list_of_probabilities_str: ' + list_of_probabilities_str)

                    try:
                        likelihood_fuction = Likelihood_fuction.objects.get(simulation_id=self.simulation_id, parameter_id=used_parameter_id)
                        likelihood_fuction.list_of_probabilities = list_of_probabilities_str
                        likelihood_fuction.nb_of_simulations = nb_of_simulations
                        likelihood_fuction.nb_of_sim_in_which_rule_was_used = nb_of_sim_in_which_rule_was_used
                        likelihood_fuction.nb_of_values_in_posterior = nb_of_values_in_posterior
                        likelihood_fuction.save()
                        print('saved to existing Likelihood_fuction ' + str(likelihood_fuction.id))

                    except:
                        likelihood_fuction = Likelihood_fuction(simulation_id=self.simulation_id, 
                                                                object_number=rule['object_number'],
                                                                parameter_id=used_parameter_id,  
                                                                list_of_probabilities=list_of_probabilities_str,
                                                                nb_of_simulations=nb_of_simulations,
                                                                nb_of_sim_in_which_rule_was_used=nb_of_sim_in_which_rule_was_used,
                                                                nb_of_values_in_posterior=nb_of_values_in_posterior)
                        likelihood_fuction.save()
                        print('saved to new Likelihood_fuction ' + str(likelihood_fuction.id))



        





    def __post_process_data(self, simulation_data_df, triggered_rules_df, errors_df, number_of_simulations):

        print('process_data_1')
        with open(self.progress_tracking_file_name, "w") as progress_tracking_file:
            progress_tracking_file.write(json.dumps({"learning_likelihoods": (len(self.rule_priors) > 0) , "nb_of_accepted_simulations_total": self.nb_of_accepted_simulations , "nb_of_accepted_simulations_current": self.nb_of_accepted_simulations , "learning__post_processing": "" , "running_monte_carlo": True, "monte_carlo__simulation_number": number_of_simulations, "monte_carlo__number_of_simulations":  number_of_simulations, "monte_carlo__post_processing":"Post-processing:  listing triggered rules"}))


        # rule_infos
        triggered_rules_df = triggered_rules_df[triggered_rules_df['triggered_rule'].notnull()]
        rule_ids = [triggered_rule_info['id'] for triggered_rule_info  in list(triggered_rules_df['triggered_rule'])]
        rule_ids = list(set(rule_ids))
        rule_info_list = list(Rule.objects.filter(id__in=rule_ids).values())
        rule_infos = {}
        for rule in rule_info_list:
            rule_infos[rule['id']] = rule
        


        # triggered_rules
        triggered_rules_per_period = triggered_rules_df.groupby(['batch_number','initial_state_id','attribute_id','period']).aggregate({'initial_state_id':'first',
                                                                                                        'batch_number':'first',
                                                                                                        'attribute_id':'first',
                                                                                                        'period':'first',
                                                                                                        'triggered_rule':list,
                                                                                                        'correct_value':'first',})  
        attribute_dict = {attribute_id: {} for attribute_id in triggered_rules_df['attribute_id'].unique().tolist()}
        triggered_rules = {}
        for batch_number in triggered_rules_df['batch_number'].unique().tolist():
            for initial_state_id in triggered_rules_df['initial_state_id'].unique().tolist():
                triggered_rules[str(initial_state_id) + '-' + str(batch_number)] = deepcopy(attribute_dict)

        for index, row in triggered_rules_per_period.iterrows():
            triggered_rules[str(row['initial_state_id']) + '-' + str(row['batch_number'])][row['attribute_id']][int(row['period'])] = {'rules': row['triggered_rule'], 'correct_value': row['correct_value']}




        # simulation_data
        print('process_data_3')
        with open(self.progress_tracking_file_name, "w") as progress_tracking_file:
            progress_tracking_file.write(json.dumps({"learning_likelihoods": (len(self.rule_priors) > 0) , "nb_of_accepted_simulations_total": self.nb_of_accepted_simulations, "nb_of_accepted_simulations_current": self.nb_of_accepted_simulations , "learning__post_processing": "" , "running_monte_carlo": "true", "monte_carlo__simulation_number": number_of_simulations, "monte_carlo__number_of_simulations":  number_of_simulations, "monte_carlo__post_processing":"Post-processing:  formatting simulated values"}))


        simulation_data = {}
        attribute_ids = [attr_id for attr_id in simulation_data_df.columns if attr_id not in ['batch_number','initial_state_id','attribute_id','period', 'randomNumber', 'cross_join_column']]
        aggregation_dict = {attr_id:list for attr_id in attribute_ids}
        aggregation_dict['batch_number'] = 'first'
        aggregation_dict['initial_state_id'] = 'first'
        simulation_data_per_entity_attribute = simulation_data_df.groupby(['batch_number','initial_state_id']).aggregate(aggregation_dict)

        for index, row in simulation_data_per_entity_attribute.iterrows():
            for attribute_id in attribute_ids:
                simulation_number = str(row['initial_state_id']) + '-' + str(row['batch_number'])
                if simulation_number not in simulation_data.keys():
                    simulation_data[str(row['initial_state_id']) + '-' + str(row['batch_number'])] = {}
                simulation_data[str(row['initial_state_id']) + '-' + str(row['batch_number'])][attribute_id] = row[attribute_id].copy()


        correct_values = self.y0_values_df.to_dict()


        # errors
        print('process_data_4')
        with open(self.progress_tracking_file_name, "w") as progress_tracking_file:
            progress_tracking_file.write(json.dumps({"learning_likelihoods": (len(self.rule_priors) > 0), "nb_of_accepted_simulations_total": self.nb_of_accepted_simulations, "nb_of_accepted_simulations_current": self.nb_of_accepted_simulations, "learning__post_processing": "" , "running_monte_carlo": True, "monte_carlo__simulation_number": number_of_simulations, "monte_carlo__number_of_simulations":  number_of_simulations, "monte_carlo__post_processing":"Post-processing:  calculating the simulated values' errors"}))


        errors = {}
        errors['score'] = 1 - errors_df['error'].mean()
        errors['correct_simulations'] = list(errors_df.loc[errors_df['error'] < 0.25, 'simulation_number'])
        errors['false_simulations'] = list(errors_df.loc[errors_df['error'] > 0.75, 'simulation_number'])



        # Front-End too slow?
        number_of_megabytes =len(json.dumps(simulation_data))/1000000
        if number_of_megabytes > 3:
            number_of_simulations_to_keep = int(len(simulation_data) * 3 / number_of_megabytes)
            keys_to_keep = list(simulation_data.keys())[:number_of_simulations_to_keep]
            simulation_data = {key:value for key, value in simulation_data.items() if key in keys_to_keep}
            triggered_rules = {key:value for key, value in triggered_rules.items() if key in keys_to_keep}
            # simulation_data = {k: d[k]) for k in keys if k in d} simulation_data
            # triggered_rules = triggered_rules[:number_of_simulations_to_send]



        simulation_model_record = Simulation_model.objects.get(id=self.simulation_id)
        simulation_model_record.rule_infos = json.dumps(rule_infos)
        simulation_model_record.triggered_rules = json.dumps(triggered_rules)
        simulation_model_record.simulation_data = json.dumps(simulation_data)
        simulation_model_record.correct_values = json.dumps(correct_values)
        simulation_model_record.errors = json.dumps(errors)
        simulation_model_record.save()







# ===========================================================================================================
 #   _____ _                 _       _   _               ______                _   _                 
 #  / ____(_)               | |     | | (_)             |  ____|              | | (_)                
 # | (___  _ _ __ ___  _   _| | __ _| |_ _  ___  _ __   | |__ _   _ _ __   ___| |_ _  ___  _ __  ___ 
 #  \___ \| | '_ ` _ \| | | | |/ _` | __| |/ _ \| '_ \  |  __| | | | '_ \ / __| __| |/ _ \| '_ \/ __|
 #  ____) | | | | | | | |_| | | (_| | |_| | (_) | | | | | |  | |_| | | | | (__| |_| | (_) | | | \__ \
 # |_____/|_|_| |_| |_|\__,_|_|\__,_|\__|_|\___/|_| |_| |_|   \__,_|_| |_|\___|\__|_|\___/|_| |_|___/

# ===========================================================================================================



    #  Rule Learning  ---------------------------------------------------------------------------------
    def likelihood_learning_simulator(self, df, rules, *rule_priors, batch_size, random_state=None):
        print('---- likelihood_learning_simulator ----')
        self.number_of_batches += 1

        print('1')
        nb_of_accepted_simulations_current = get_nb_of_accepted_simulations_current(self)
        with open(self.progress_tracking_file_name, "w") as progress_tracking_file:
            progress_dict_string = json.dumps({"learning_likelihoods": True, "nb_of_accepted_simulations_total": self.nb_of_accepted_simulations, "nb_of_accepted_simulations_current": nb_of_accepted_simulations_current , "learning__post_processing": "" , "running_monte_carlo": False })
            progress_tracking_file.write(progress_dict_string)

        print('2')
        for rule_nb in range(len(rules)):
            rules[rule_nb]['rule_was_used_in_simulation'] = [False]*batch_size
            rule = rules[rule_nb]

            if rule['learn_posterior']:
                if not rule['has_probability_1']:
                    df['triggerThresholdForRule' + str(rule['id'])] = rule_priors[rule['prior_index']]
                for used_parameter_id in rule['used_parameter_ids']:
                   df['param' + str(used_parameter_id)] = rule_priors[rule['parameters'][used_parameter_id]['prior_index']]
            else:
                if not rule['has_probability_1']:
                    df['triggerThresholdForRule' + str(rule['id'])] =  rv_histogram(rule['histogram']).rvs(size=batch_size)
                for used_parameter_id in rule['used_parameter_ids']:
                   df['param' + str(used_parameter_id)] = rv_histogram(rule['parameters'][used_parameter_id]['histogram']).rvs(size=batch_size)


        print('3')
        if self.is_timeseries_analysis: 
            times = np.arange(self.simulation_start_time + self.timestep_size, self.simulation_end_time, self.timestep_size)
            df['delta_t'] = self.timestep_size
        else:
            times = [self.simulation_start_time, self.simulation_end_time]
            df[self.y0_columns] = None


        print('4')
        y0_values_in_simulation = pd.DataFrame(index=range(batch_size))
        for period in range(len(times)-1):
            df['randomNumber'] = np.random.random(batch_size)
            for rule in rules:
                if rule['is_conditionless']:
                    if rule['has_probability_1']:
                        satisfying_rows = [True] * batch_size
                    else:
                        satisfying_rows = pd.eval('df.randomNumber < df.triggerThresholdForRule' + str(rule['id']))
                        
                else:
                    if rule['has_probability_1']:
                        condition_satisfying_rows = pd.eval(rule['condition_exec'])
                        satisfying_rows = condition_satisfying_rows
                    else:
                        condition_satisfying_rows = pd.eval('df.randomNumber < df.triggerThresholdForRule' + str(rule['id']))
                        triggered_rules = pd.eval(rule['condition_exec'])
                        satisfying_rows = condition_satisfying_rows & triggered_rules 

                # --------  used rules  --------
                if rule['learn_posterior']:
                    rule['rule_was_used_in_simulation'] = rule['rule_was_used_in_simulation'] | condition_satisfying_rows


                # --------  THEN  --------
                if rule['effect_is_calculation']: 
                    new_values = pd.eval(rule['effect_exec'])
                    if rule['changed_var_data_type'] in ['relation','int']:
                        nan_rows = new_values.isnull()
                        new_values = new_values.fillna(0)
                        new_values = new_values.astype(int)
                        new_values[nan_rows] = np.nan
                    elif rule['changed_var_data_type'] == 'real':
                        new_values = new_values.astype(float)
                    elif rule['changed_var_data_type'] == 'boolean':
                        nan_rows = new_values.isnull()
                        new_values = new_values.astype(bool)
                        new_values[nan_rows] = np.nan
                    elif rule['changed_var_data_type'] in ['string','date']:
                        nan_rows = new_values.isnull()
                        new_values = new_values.astype(str)
                        new_values[nan_rows] = np.nan

                else:
                    new_values = json.loads(rule['effect_exec'])

                # print('XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX')
                # print('XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX')
                # if rule['id'] ==21:
                #     print(df['param23'])
                #     if 'condition_satisfying_rows' in locals():
                #         print('---condition_satisfying_rows------------------------------------')
                #         print(condition_satisfying_rows)
                #     print('---satisfying_rows---------------------------------------------------')
                #     print(satisfying_rows)
                #     print('===========================================')
                #     print('---df.obj1attr169---------------------------------------------------')
                #     print(df['obj1attr169'])
                #     print('---new_values---------------------------------------------------')
                #     print(new_values)
                # print('XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX')
                # print('XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX')


                # =========================  THE MOST IMPORTANT LINE  ===============================
                df.loc[satisfying_rows,rule['column_to_change']] = new_values  
                # ===================================================================================


            print('%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%')
            print(len(df))
            print(df.columns)
            print(self.y0_columns)
            y0_values_in_this_period = pd.DataFrame(df[self.y0_columns])
            y0_values_in_this_period.columns = [col + 'period' + str(period) for col in y0_values_in_this_period.columns] #faster version
            y0_values_in_simulation = y0_values_in_simulation.join(y0_values_in_this_period)

            # merging_columns =  ['obj' + obj_num + 'attrobject_id' for obj_num in self.objects_dict.keys()] #slower, safer version
            # y0_values_in_simulation = pd.merge(y0_values_in_simulation, y0_values_in_this_period, on=merging_columns, how='outer', suffixes=['','period' + period])

        for rule in rules:  
            if rule['learn_posterior']:
                # y0_values_in_simulation['triggerThresholdForRule' + str(rule['id'])] = rule_priors[rule['prior_index']]
                # rule['rule_was_used_in_simulation'].index = range(len(rule['rule_was_used_in_simulation']))

                y0_values_in_simulation['rule_used_in_simulation_' + str(rule['id'])] = rule['rule_was_used_in_simulation']
                del rule['rule_was_used_in_simulation']

        y0_values_in_simulation = pd.concat([y0_values_in_simulation,df[self.parameter_columns]], axis=1)
        y0_values_in_simulation.index = range(len(y0_values_in_simulation))
        return y0_values_in_simulation.to_dict('records')

          





    #  Monte-Carlo  ---------------------------------------------------------------------------------
    def __run_monte_carlo_simulation(self, nb_of_simulations=300):
        print('¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬  __run_monte_carlo_simulation   ¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬')
        y0 = np.asarray(self.df[self.y0_columns].copy())
        batch_size = len(y0)

        simulation_data_df = pd.DataFrame()
        triggered_rules_df = pd.DataFrame()
        errors_df = pd.DataFrame()

        number_of_batches = math.ceil(nb_of_simulations/batch_size)
        for batch_number in range(number_of_batches):

            with open(self.progress_tracking_file_name, "w") as progress_tracking_file:
                progress_dict_string = json.dumps({"learning_likelihoods": (len(self.rule_priors) > 0), "nb_of_accepted_simulations_total": self.nb_of_accepted_simulations, "nb_of_accepted_simulations_current": self.nb_of_accepted_simulations, "learning__post_processing": "" , "running_monte_carlo": "true", "monte_carlo__simulation_number": (batch_number*batch_size), "monte_carlo__number_of_simulations":  nb_of_simulations, "monte_carlo__post_processing":""})
                progress_tracking_file.write(progress_dict_string)

            print('run_monte_carlo_simulation_1')
            df = self.df.copy()
            if not self.is_timeseries_analysis: 
                df[self.y0_columns] = None

            for rule in self.rules:
                if not rule['has_probability_1']:
                    df['triggerThresholdForRule' + str(rule['id'])] =  rv_histogram(rule['histogram']).rvs(size=batch_size)
                for used_parameter_id in rule['used_parameter_ids']:
                    print('=======  rule[\'parameter_histograms\']  ===============================================')
                    print(used_parameter_id)
                    print(str(rule['parameters'][used_parameter_id]['histogram']))
                    df['param' + str(used_parameter_id)] = rv_histogram(rule['parameters'][used_parameter_id]['histogram']).rvs(size=batch_size)

            print('run_monte_carlo_simulation_2')
            if self.is_timeseries_analysis: 
                times = np.arange(self.simulation_start_time + self.timestep_size, self.simulation_end_time, self.timestep_size)
                df['delta_t'] = self.timestep_size
            else:
                times = [self.simulation_start_time, self.simulation_end_time]


            print('run_monte_carlo_simulation_3')
            y0_values_in_simulation = pd.DataFrame(index=range(batch_size))
            for period in range(len(times)-1):

                df['randomNumber'] = np.random.random(batch_size)
                for rule in self.rules:

                    # Apply Rule  ================================================================
                    if rule['is_conditionless']:
                        if rule['has_probability_1']:
                            satisfying_rows = [True] * batch_size
                            condition_satisfying_rows = [True] * batch_size
                            trigger_thresholds = [0] * batch_size
                        else:
                            satisfying_rows = pd.eval('df.randomNumber < df.triggerThresholdForRule' + str(rule['id'])).tolist()
                            condition_satisfying_rows = [True] * batch_size
                            trigger_thresholds = list(df['triggerThresholdForRule' + str(rule['id'])])

                    else:
                        if rule['has_probability_1']:
                            satisfying_rows = pd.eval(str(rule['condition_exec'])).tolist()
                            condition_satisfying_rows = pd.eval(str(rule['condition_exec']))
                            trigger_thresholds = [0] * batch_size
                        else:
                            satisfying_rows = pd.eval('df.randomNumber < df.triggerThresholdForRule' + str(rule['id']) + '  & ' + str(rule['condition_exec'])).tolist()
                            condition_satisfying_rows = pd.eval(str(rule['condition_exec']))
                            trigger_thresholds = list(df['triggerThresholdForRule' + str(rule['id'])])
                    
                    # print('YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY')
                    # print('YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY')
                    # print(rule['id'])
                    # print('--------------------------------------------------------------------')
                    # print(satisfying_rows)
                    # print('--------------------------------------------------------------------')
                    # print(condition_satisfying_rows)
                    # print('--------------------------------------------------------------------')
                    # print(trigger_thresholds)
                    # print('YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY')
                    # print('YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY')
                    print('run_monte_carlo_simulation_4')
                    if rule['effect_is_calculation']:
                        all_new_values = pd.eval(rule['effect_exec'])
                        if rule['changed_var_data_type'] in ['relation','int']:
                            nan_rows = all_new_values.isnull()
                            all_new_values = all_new_values.fillna(0)
                            all_new_values = all_new_values.astype(int)
                            all_new_values[nan_rows] = np.nan
                        elif rule['changed_var_data_type'] == 'real':
                            all_new_values = all_new_values.astype(float)
                        elif rule['changed_var_data_type'] == 'boolean':
                            nan_rows = all_new_values.isnull()
                            all_new_values = all_new_values.astype(bool)
                            all_new_values[nan_rows] = np.nan
                        elif rule['changed_var_data_type'] in ['string','date']:
                            nan_rows = all_new_values.isnull()
                            all_new_values = all_new_values.astype(str)
                            all_new_values[nan_rows] = np.nan

                    else:
                        all_new_values = [json.loads(rule['effect_exec'])] * batch_size

                    print('run_monte_carlo_simulation_5')
                    new_values = [value for value, satisfying in zip(all_new_values,satisfying_rows) if satisfying]
                    df.loc[satisfying_rows,rule['column_to_change']] = new_values




                    # Save the Simulation State  =======================================================
                    # if rule['is_conditionless']: 
                    #     trigger_thresholds = [0] * batch_size
                    # else:
                    #     trigger_thresholds = list(df['triggerThresholdForRule' + str(rule['id'])])


                    calculated_values = list(df[rule['column_to_change']])
                    errors = np.zeros(len(calculated_values))
                    correct_value = ['unknown'] * len(calculated_values)
                    if rule['column_to_change'] in self.y0_columns:
                        errors = self.error_of_single_values(np.array(calculated_values), rule['column_to_change'], period)
                        correct_value = list(self.y0_values_df[rule['column_to_change'] + 'period' + str(period)])


                    triggered_rule_infos_df = pd.DataFrame({'condition_satisfied': condition_satisfying_rows,
                                                            'id':[rule['id']]* batch_size,
                                                            'pt': satisfying_rows,          # pt = probability_triggered
                                                            'tp': trigger_thresholds,       # tp = trigger_probability
                                                            'v': calculated_values,         # v = new_value
                                                            'error':errors})

                    print('run_monte_carlo_simulation_6')
                    triggered_rule_infos = triggered_rule_infos_df.to_dict('records')
                    triggered_rule_infos = [rule_info if rule_info['condition_satisfied'] else None for rule_info in triggered_rule_infos]
                    for i in range(len(triggered_rule_infos)):
                        if triggered_rule_infos[i] is not None:
                                del triggered_rule_infos[i]['condition_satisfied']
                                if np.isnan(triggered_rule_infos[i]['error']):
                                    del triggered_rule_infos[i]['error']


                    currently_triggered_rules = pd.DataFrame({  'initial_state_id':df.index,
                                                                'batch_number':[batch_number]*batch_size,
                                                                'attribute_id':[rule['column_to_change']]*batch_size,
                                                                'period':[period]*batch_size,
                                                                'triggered_rule': triggered_rule_infos, 
                                                                'correct_value': correct_value
                                                                })
                    print('run_monte_carlo_simulation_7')

                    triggered_rules_df = triggered_rules_df.append(currently_triggered_rules)

                
                # simulated values
                print('run_monte_carlo_simulation_8')
                df['initial_state_id'] = df.index
                df['batch_number'] = batch_number
                df['period'] = period
                simulation_data_df = simulation_data_df.append(df)

                # error
                y0_values_in_this_period = pd.DataFrame(df[self.y0_columns])
                y0_values_in_this_period.columns = [col + 'period' + str(period) for col in y0_values_in_this_period.columns] #faster version
                y0_values_in_simulation = y0_values_in_simulation.join(y0_values_in_this_period)

            print('run_monte_carlo_simulation_9')
            errors = self.n_dimensional_distance(y0_values_in_simulation.to_dict('records'), self.y0_values)
            error_df = pd.DataFrame({  'simulation_number': [str(index) + '-' + str(batch_number) for index in df.index],
                                        'error': errors})
            errors_df = errors_df.append(error_df)


        return (simulation_data_df, triggered_rules_df, errors_df)











# ===========================================================================================================
#               _     _ _ _   _                   _    ______ _  __ _    _   _           _           
#      /\      | |   | (_) | (_)                 | |  |  ____| |/ _(_)  | \ | |         | |          
#     /  \   __| | __| |_| |_ _  ___  _ __   __ _| |  | |__  | | |_ _   |  \| | ___   __| | ___  ___ 
#    / /\ \ / _` |/ _` | | __| |/ _ \| '_ \ / _` | |  |  __| | |  _| |  | . ` |/ _ \ / _` |/ _ \/ __|
#   / ____ \ (_| | (_| | | |_| | (_) | | | | (_| | |  | |____| | | | |  | |\  | (_) | (_| |  __/\__ \
#  /_/    \_\__,_|\__,_|_|\__|_|\___/|_| |_|\__,_|_|  |______|_|_| |_|  |_| \_|\___/ \__,_|\___||___/
# 
# ===========================================================================================================

    def unchanged(self, y):
        return y



    def categorical_distance(self, u, v):
        u = np.asarray(u, dtype=object, order='c').squeeze()
        u = np.atleast_1d(u)
        v = np.asarray(v, dtype=object, order='c').squeeze()
        v = np.atleast_1d(v)
        u_v = 1. - np.equal(u, v).astype(int)
        return u_v





    def n_dimensional_distance(self, u, v):
        # u = simulated values;  v = correct_values
        u = np.asarray(u, dtype=object, order='c').squeeze()
        u = np.atleast_1d(u)
        v = np.asarray(v, dtype=object, order='c').squeeze()
        v = np.atleast_1d(v)
        u_df = pd.DataFrame(list(u))
        v_df = pd.DataFrame(list(v))
        u_df = u_df.fillna(np.nan)
        v_df = v_df.fillna(np.nan)
        
        total_error = np.zeros(shape=len(u))
        dimensionality = np.zeros(shape=len(u))
        for y0_column in self.y0_columns:
            period_columns = [col for col in u_df.columns if col.split('period')[0] == y0_column]
            if self.y0_column_dt[y0_column] in ['string','bool','relation']:
                for period_column in period_columns:
                    error = 1. - np.equal(np.array(u_df[period_column]), np.array(v_df[period_column])).astype(int)
                    error[pd.isnull(v_df[period_column])] = 0 # set the error to zero where the correct value was not given
                    total_error += error
                    dimensionality += 1 - np.array(np.logical_or(v_df[period_column].isnull(),u_df[period_column].isnull()).astype(int))
            if self.y0_column_dt[y0_column] in ['int','real']:
                for period_column in period_columns:
                    period_number = max(int(period_column.split('period')[1]), 1)
                    # print('^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v')
                    # print(str(list(v_df[period_column.split('period')[0]])))
                    # print(str(period_number))
                    # print('^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v')
                    true_change_percent_per_period = ((np.array(v_df[period_column]) - np.array(v_df[period_column.split('period')[0]]))/np.array(v_df[period_column.split('period')[0]]))/period_number
                    simulated_change_percent_per_period = ((np.array(u_df[period_column]) - np.array(v_df[period_column.split('period')[0]]))/np.array(v_df[period_column.split('period')[0]]))/period_number
                    error_of_value_change = np.minimum(np.abs(simulated_change_percent_per_period - true_change_percent_per_period) * 20,1)
                    error = np.minimum(error_of_value_change, 1)
                    # residuals = np.abs(np.array(u_df[period_column]) - np.array(v_df[period_column]))
                    # error_in_value_range = residuals/np.nanmax([(np.nanmax(v_df[period_column]) - np.nanmin(v_df[period_column])), 0.00000001])
                    # error_in_error_range =  residuals/np.nanmax(residuals)
                    # error = np.minimum(error_in_value_range + error_in_error_range, 1)
                    dimensionality += 1 -np.isnan(error).astype('int')
                    error[np.isnan(error)] = 0
                    error[pd.isnull(v_df[period_column])] = 0# set the error to zero where the correct value was not given
                    total_error += error 

        dimensionality = np.maximum(dimensionality, [1]*len(u))
        error = total_error/dimensionality


        # posterior_values_to_delete   (delete value from posterior if it's rule was not used in the simulation)
        if self.currently_running_learn_likelihoods:
            for rule in self.rules:
                if rule['learn_posterior']:
                    to_be_deleted_rows = np.array(error < 0.5)  &  np.invert(u_df['rule_used_in_simulation_' + str(rule['id'])])
                    posterior_value_rows = np.array(error < 0.5)  &  u_df['rule_used_in_simulation_' + str(rule['id'])]
                    if not rule['has_probability_1']:
                        self.posterior_values_to_delete[rule['id']].extend(list(u_df.loc[to_be_deleted_rows, 'triggerThresholdForRule' + str(rule['id'])]))
                        # ================ TESTING =======================================
                        self.posterior_values[rule['id']].extend(list(u_df.loc[posterior_value_rows, 'triggerThresholdForRule' + str(rule['id'])]))
                        # ================================================================

                    parameter_columns = [col for col in u_df.columns if len(col.split('param'))>1]
                    for parameter_column in parameter_columns:

                        self.posterior_values_to_delete[parameter_column].extend(list(u_df.loc[to_be_deleted_rows, parameter_column]))
                        # print('========================================================================')
                        # print('===============  posterior_values_to_delete  ===========================')
                        # print('========================================================================')
                        # print(sum(to_be_deleted_rows))
                        # print(u_df[to_be_deleted_rows])
                        # print(len(u_df.loc[to_be_deleted_rows, parameter_column]))
                        # print('---')
                        # ================ TESTING =======================================
                        self.posterior_values[parameter_column].extend(list(u_df.loc[posterior_value_rows, parameter_column]))
                        # ================================================================
        return error
            

    def error_of_single_value(self, all_calculated_values, column_name, row_index, period):
        initial_value = np.array(self.df[column_name])[row_index]
        calculated_value = all_calculated_values[row_index]     

        all_correct_values = np.array(self.y0_values_df[column_name + 'period' + str(period)])
        correct_value = all_correct_values[row_index]
        # self.y0_values[row_index][column_name + 'period' + str(period)]

        if self.y0_column_dt[column_name] in ['string','bool','relation']:

            error = 1. - int(calculated_value == correct_value)
        if self.y0_column_dt[column_name] in ['int','real']:
            # residual = np.abs(calculated_value - correct_value)
            # all_residuals = np.abs(all_calculated_values - all_correct_values)
            # error_in_value_range = residual/(np.max(all_correct_values) - np.min(all_correct_values))
            # error_in_error_range =  residual/np.max(all_residuals)
            # error = error_in_value_range + error_in_error_range 

            true_change_percent_per_period = ((correct_value - initial_value)/initial_value)/max(period,1)
            simulated_change_percent_per_period = ((np.array(calculated_value) - initial_value)/initial_value)/max(period,1)
            error_of_value_change = np.minimum(np.abs(simulated_change_percent_per_period - true_change_percent_per_period) * 20,1)
            error = np.minimum(error_of_value_change, 1)

        return error



    def error_of_single_values(self, calculated_values, column_name, period):      
        initial_values = np.array(self.df[column_name])
        correct_values = np.array(self.y0_values_df[column_name + 'period' + str(period)])


        if self.y0_column_dt[column_name] in ['string','bool','relation']:
            errors = 1. - np.equal(np.array(calculated_values), np.array(correct_values)).astype(int)
        if self.y0_column_dt[column_name] in ['int','real']:
            # residuals = np.abs(np.array(calculated_values) - np.array(correct_values))
            # error_in_value_range = residuals/(np.max(correct_values) - np.min(correct_values))
            # error_in_error_range =  residuals/np.max(residuals)
            # errors = np.minimum(error_in_value_range + error_in_error_range, 1)  

            true_change_percent_per_period = ((correct_values - initial_values)/initial_values)/max(period,1)
            simulated_change_percent_per_period = ((np.array(calculated_values) - initial_values)/initial_values)/max(period,1)
            error_of_value_change = np.minimum(np.abs(simulated_change_percent_per_period - true_change_percent_per_period) * 20,1)
            errors = np.minimum(error_of_value_change, 1)

        return errors



    def reduce_number_of_rows(self, df, max_nb_of_rows):

        if len(df)> max_nb_of_rows:
            number_of_nulls_df = df.isnull().sum(1)
            actual_y0_columns = [col for col in df.columns if col.split('period')[0] in self.y0_columns]
            number_of_y0_nulls_df = df[actual_y0_columns].isnull().sum(1)
            score_df = 0.35 * (1 - number_of_nulls_df/max(number_of_nulls_df)) + 0.65 * (1 - number_of_y0_nulls_df/max(number_of_y0_nulls_df))

            reduced_df = score_df[score_df < 0.5]
            if len(reduced_df) > max_nb_of_rows: 
                # select random rows from amongst the rows with minimal score = 0.5
                df = df.loc[reduced_df.index]
                df = df.sample(n=max_nb_of_rows)
            elif len(number_of_nulls_df[number_of_nulls_df < (max_number_of_nulls/2)]) > max_nb_of_rows: 
                # select random rows from amongst the rows with minimal score = 0.25
                less_reduced_df = score_df[score_df < 0.25]
                df = df.loc[less_reduced_df.index]
                df = df.sample(n=max_nb_of_rows)
            else:
                # select random rows
                df = df.sample(n=max_nb_of_rows)

        return df



    # ==========================================================================================
    #  Getter-Functions
    # =======================================================================================


    def get_rule_priors(self):
        return self.rule_priors



   




def get_nb_of_accepted_simulations_current(simulation_class):
    # ELFI's Progressbar shows the number of completed batches vs. the number of expected batches
    # i.e.: simulation_class.elfi_sampler.state['n_batches']  vs.  simulation_class.elfi_sampler._objective_n_batches
    if simulation_class.elfi_sampler.state['samples'] is not None:
        return len(simulation_class.elfi_sampler.state['samples'].keys())
    else:
        return 0
