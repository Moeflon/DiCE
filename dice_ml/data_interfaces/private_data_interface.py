"""Module containing meta data information about private data."""

import sys
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
import collections
from collections import OrderedDict
import logging
logging.basicConfig(level=logging.NOTSET)
from sklearn.preprocessing import LabelEncoder

class PrivateData:
    """A data interface for private data with meta information."""

    def __init__(self, params):
        """Init method

        :param features: Dictionary or OrderedDict with feature names as keys and range in int/float (for continuous features) or categories in string (for categorical features) as values. For python version <=3.6, should provide only an OrderedDict.
        :param outcome_name: Outcome feature name.
        :param normalize: if False, do not normalize continuous features
        :param type_and_precision (optional): Dictionary with continuous feature names as keys. If the feature is of type int, just string 'int' should be provided, if the feature is of type float, a list of type and precision should be provided. For instance, type_and_precision: {cont_f1: 'int', cont_f2: ['float', 2]} for continuous features cont_f1 and cont_f2 of type int and float (and precision up to 2 decimal places) respectively. Default value is None and all features are treated as int.
        :param mad (optional): Dictionary with feature names as keys and corresponding Median Absolute Deviations (MAD) as values. Default MAD value is 1 for all features.
        :param data_name (optional): Dataset name
        :param one_hot (optional): If False, do not one-hot encode
        """

        if sys.version_info > (3,6,0) and type(params['features']) in [dict, collections.OrderedDict]:
            features_dict = params['features']
        elif sys.version_info <= (3,6,0) and type(params['features']) is collections.OrderedDict:
            features_dict = params['features']
        else:
            raise ValueError(
                "should provide dictionary with feature names as keys and range (for continuous features) or categories (for categorical features) as values. For python version <3.6, should provide an OrderedDict")

        if type(params['outcome_name']) is str:
            self.outcome_name = params['outcome_name']
        else:
            raise ValueError("should provide the name of outcome feature")
        
        if 'one_hot' in params:
            self.one_hot = params['one_hot']
        else:
            self.one_hot = True
            
        if 'continuous_features' not in params:
            raise ValueError("should provide list of continuous features")
            
        if 'type_and_precision' in params:
            self.type_and_precision = params['type_and_precision']
        else:
            self.type_and_precision = {}

        if 'quantiles' in params:
            self.quantiles = params['quantiles']
        else:
            self.quantiles = {}
            
        if 'normalize' in params:
            self.normalize = params['normalize']
        else:
            self.normalize = True

        self.continuous_feature_names = []
        self.permitted_range = {}
        self.categorical_feature_names = []
        self.categorical_levels = {}

        for feature in features_dict:
            if feature in params['continuous_features']:  # continuous feature
                self.continuous_feature_names.append(feature)
                self.permitted_range[feature] = features_dict[feature]
            else:
                self.categorical_feature_names.append(feature)
                self.categorical_levels[feature] = features_dict[feature]

        if 'mad' in params:
            self.mad = params['mad']
        else:
            self.mad = {}

        # self.continuous_feature_names + self.categorical_feature_names
        self.feature_names = list(features_dict.keys())

        self.continuous_feature_indexes = [list(features_dict.keys()).index(
            name) for name in self.continuous_feature_names if name in features_dict]

        self.categorical_feature_indexes = [list(features_dict.keys()).index(
            name) for name in self.categorical_feature_names if name in features_dict]

        for feature_name in self.continuous_feature_names:
            if feature_name not in self.type_and_precision:
                self.type_and_precision[feature_name] = 'int'

                # # Initializing a label encoder to obtain label-encoded values for categorical variables
                # self.labelencoder = {}
                #
                # self.label_encoded_data = {}
                #
                # for column in self.categorical_feature_names:
                #     self.labelencoder[column] = LabelEncoder()
                #     self.label_encoded_data[column] = self.labelencoder[column].fit_transform(self.categorical_levels[column])

                # self.max_range = -np.inf
                # for feature in self.continuous_feature_names:
                #     self.max_range = max(self.max_range, self.permitted_range[feature][1])

        if 'data_name' in params:
            self.data_name = params['data_name']
        else:
            self.data_name = 'mydata'

    def one_hot_encode_data(self, data):
        """One-hot-encodes the data."""
        return pd.get_dummies(data, drop_first=False, columns=self.categorical_feature_names)

    
    def get_quantiles_from_training_data(self, quantile=0.05, normalized=False):
        """Computes required quantile of Absolute Deviations of features."""
        return self.quantiles
    
    def normalize_data(self, df, encoding='one-hot'):
        """Normalizes continuous features to make them fall in the range [0,1]."""
        result = df.copy()

        if self.normalize:
            for feature_name in self.continuous_feature_names:
                max_value = self.permitted_range[feature_name][1]
                min_value = self.permitted_range[feature_name][0]
                result[feature_name] = (df[feature_name] - min_value) / (max_value - min_value)

        # if encoding == 'label': # need not do this if not required
        #     for ix in self.categorical_feature_indexes:
        #         feature_name = self.feature_names[ix]
        #         max_value = len(self.categorical_levels[feature_name])-1
        #         min_value = 0
        #         result[feature_name] = (df[feature_name] - min_value) / (max_value - min_value)
        return result

    def de_normalize_data(self, df):
        """De-normalizes continuous features from [0,1] range to original range."""
        if len(df) == 0 or not self.normalize:
            return df
        result = df.copy()
        for feature_name in self.continuous_feature_names:
            max_value = self.permitted_range[feature_name][1]
            min_value = self.permitted_range[feature_name][0]
            result[feature_name] = (
                df[feature_name]*(max_value - min_value)) + min_value
        return result

    def get_minx_maxx(self, normalized=True):
        """Gets the min/max value of features in normalized or de-normalized form."""
        minx = np.array([[0.0]*len(self.ohe_encoded_feature_names)])
        maxx = np.array([[1.0]*len(self.ohe_encoded_feature_names)])

        if normalized:
            return minx, maxx
        else:
            for idx, feature_name in enumerate(self.continuous_feature_names):
                minx[0][idx] = self.permitted_range[feature_name][0]
                maxx[0][idx] = self.permitted_range[feature_name][1]
            return minx, maxx

    def get_mads(self, normalized=True):
        """Computes Median Absolute Deviation of features."""
        if normalized is False:
            return self.mad.copy()
        else:
            mads = {}
            for feature in self.continuous_feature_names:
                if feature in self.mad:
                    mads[feature] = (self.mad[feature])/(self.permitted_range[feature][1] - self.permitted_range[feature][0])
            return mads

    def get_valid_mads(self, normalized=False, display_warnings=False, return_mads=True):
        """Computes Median Absolute Deviation of features. If they are <=0, returns a practical value instead"""
        mads = self.get_mads(normalized=normalized)
        for feature in self.continuous_feature_names:
            if feature in mads:
                if mads[feature] <= 0:
                    mads[feature] = 1.0
                    if display_warnings:
                        logging.warning(" MAD for feature %s is 0, so replacing it with 1.0 to avoid error.", feature)
            else:
                mads[feature] = 1.0
                if display_warnings:
                    logging.info(" MAD is not given for feature %s, so using 1.0 as MAD instead.", feature)

        if return_mads:
            return mads

    def create_ohe_params(self):
        if len(self.categorical_feature_names) > 0 and self.one_hot:
            # simulating sklearn's one-hot-encoding
            # continuous features on the left
            self.ohe_encoded_feature_names = [
                feature for feature in self.continuous_feature_names]
            for feature_name in self.categorical_feature_names:
                for category in sorted(self.categorical_levels[feature_name]):
                    self.ohe_encoded_feature_names.append(
                        feature_name+'_'+str(category))
        else:
            # one-hot-encoded data is same as original data if there is no categorical features.
            self.ohe_encoded_feature_names = [feat for feat in self.feature_names]

        self.ohe_base_df = self.prepare_df_for_ohe_encoding() # base dataframe for doing one-hot-encoding
        # ohe_encoded_feature_names and ohe_base_df are created (and stored as data class's parameters) when get_data_params_for_gradient_dice() is called from gradient-based DiCE explainers

    def get_data_params_for_gradient_dice(self):
        """Gets all data related params for DiCE."""

        self.create_ohe_params()
        minx, maxx = self.get_minx_maxx(normalized=self.normalize)

        # get the column indexes of categorical and continuous features after one-hot-encoding
        encoded_categorical_feature_indexes = self.get_encoded_categorical_feature_indexes()
        flattened_indexes = [item for sublist in encoded_categorical_feature_indexes for item in sublist]
        encoded_continuous_feature_indexes = [ix for ix in range(len(minx[0])) if ix not in flattened_indexes]

        # min and max for continuous features in original scale
        org_minx, org_maxx = self.get_minx_maxx(normalized=False)
        cont_minx = list(org_minx[0][encoded_continuous_feature_indexes])
        cont_maxx = list(org_maxx[0][encoded_continuous_feature_indexes])

        # decimal precisions for continuous features
        cont_precisions = [self.get_decimal_precisions()[ix] for ix in range(len(self.continuous_feature_names))]

        return minx, maxx, encoded_categorical_feature_indexes, encoded_continuous_feature_indexes, cont_minx, cont_maxx, cont_precisions


    def get_encoded_categorical_feature_indexes(self):
        """Gets the column indexes categorical features after one-hot-encoding."""
        cols = []
        for col_parent in self.categorical_feature_names:
            temp = [self.ohe_encoded_feature_names.index(
                col) for col in self.ohe_encoded_feature_names if col.startswith(col_parent) and
                   col not in self.continuous_feature_names]
            cols.append(temp)
        return cols

    def get_indexes_of_features_to_vary(self, features_to_vary='all'):
        """Gets indexes from feature names of one-hot-encoded data."""
        if features_to_vary == "all":
            return [i for i in range(len(self.ohe_encoded_feature_names))]
        else:
            ixs = []
            encoded_cats_ixs = self.get_encoded_categorical_feature_indexes()
            encoded_cats_ixs = [item for sublist in encoded_cats_ixs for item in sublist]
            for colidx, col in enumerate(self.encoded_feature_names):
                if colidx in encoded_cats_ixs and col.startswith(tuple(features_to_vary)):
                    ixs.append(colidx)
                elif colidx not in encoded_cats_ixs and col in features_to_vary:
                    ixs.append(colidx)
            return ixs

    def from_label(self, data):
        """Transforms label encoded data back to categorical values"""
        out = data.copy()
        if isinstance(data, pd.DataFrame) or isinstance(data, dict):
            for column in self.categorical_feature_names:
                out[column] = self.labelencoder[column].inverse_transform(out[column].round().astype(int).tolist())
            return out
        elif isinstance(data, list):
            for column in self.categorical_feature_indexes:
                out[column] = self.labelencoder[self.feature_names[column]].inverse_transform([round(out[column])])[0]
            return out

    def from_dummies(self, data, prefix_sep='_'):
        """Gets the original data from dummy encoded data with k levels."""
        out = data.copy()
        for l in self.categorical_feature_names:
            cols, labs = [[c.replace(
                x, "") for c in data.columns if c.startswith(l+prefix_sep)] for x in ["", l+prefix_sep]]
            
            out[l] = pd.Categorical(
                np.array(labs)[np.argmax(data[cols].values, axis=1)])
            
            out.drop(cols, axis=1, inplace=True)
        return out

    def get_decimal_precisions(self):
        """"Gets the precision of continuous features in the data."""
        precisions = [0]*len(self.continuous_feature_names)
        for ix, feature_name in enumerate(self.continuous_feature_names):
            type_prec = self.type_and_precision[feature_name]
            if type_prec == 'int':
                precisions[ix] = 0
            else:
                precisions[ix] = self.type_and_precision[feature_name][1]
        return precisions

    def get_decoded_data(self, data, encoding='one-hot'):
        """Gets the original data from encoded data."""
        if len(data) == 0:
            return data

        index = [i for i in range(0, len(data))]
        if self.one_hot:
            if isinstance(data, pd.DataFrame):
                return self.from_dummies(data)
            elif isinstance(data, np.ndarray):
                data = pd.DataFrame(data=data, index=index,
                                    columns=self.ohe_encoded_feature_names)
                return self.from_dummies(data)
            else:
                raise ValueError("data should be a pandas dataframe or a numpy array")

        else:
            data = pd.DataFrame(data=data, index=index,
                                columns=self.feature_names)
            return data

    def prepare_df_for_ohe_encoding(self):
        """Create base dataframe to do OHE for a single instance or a set of instances"""
        levels = []
        colnames = [feat for feat in self.categorical_feature_names]
        for cat_feature in colnames:
            levels.append(self.categorical_levels[cat_feature])

        if len(colnames) > 0:
            df = pd.DataFrame({colnames[0]: levels[0]})
        else:
            df = pd.DataFrame()

        for col in range(1, len(colnames)):
            temp_df = pd.DataFrame({colnames[col]: levels[col]})
            df = pd.concat([df, temp_df], axis=1, sort=False)

        colnames = [feat for feat in self.continuous_feature_names]
        for col in range(0, len(colnames)):
            temp_df = pd.DataFrame({colnames[col]: []})
            df = pd.concat([df, temp_df], axis=1, sort=False)

        return df

    def prepare_query_instance(self, query_instance):
        """Prepares user defined test input(s) for DiCE."""
        if isinstance(query_instance, list):
            if isinstance(query_instance[0], dict):  # prepare a list of query instances
                test = pd.DataFrame(query_instance, columns=self.feature_names)

            else:  # prepare a single query instance in list
                query_instance = {'row1': query_instance}
                test = pd.DataFrame.from_dict(
                    query_instance, orient='index', columns=self.feature_names)

        elif isinstance(query_instance, dict):
            test = pd.DataFrame({k: [v] for k, v in query_instance.items()}, columns=self.feature_names)

        elif isinstance(query_instance, pd.DataFrame):
            test = query_instance.copy()

        else:
            raise ValueError("Query instance should be a dict, a pandas dataframe, a list, or a list of dicts")

        test = test.reset_index(drop=True)
        return test

    def get_ohe_min_max_normalized_data(self, query_instance):
        """Transforms query_instance into one-hot-encoded and min-max normalized data. query_instance should be a dict, a dataframe, a list, or a list of dicts"""
        temp = query_instance = self.prepare_query_instance(query_instance)
        if self.one_hot:
            query_instance[self.categorical_feature_names] = query_instance[self.categorical_feature_names].astype(int)
            temp = self.ohe_base_df.append(query_instance, ignore_index=True, sort=False)
            temp = self.one_hot_encode_data(temp)
            temp = temp.tail(query_instance.shape[0]).reset_index(drop=True)
        return self.normalize_data(temp) # returns a pandas dataframe

    def get_inverse_ohe_min_max_normalized_data(self, transformed_data):
        """Transforms one-hot-encoded and min-max normalized data into raw user-fed data format. transformed_data should be a dataframe or an array"""
        raw_data = self.get_decoded_data(transformed_data, encoding='one-hot')
        raw_data = self.de_normalize_data(raw_data)
        precisions = self.get_decimal_precisions()
        for ix, feature in enumerate(self.continuous_feature_names):
            raw_data[feature] = raw_data[feature].astype(float).round(precisions[ix])
        raw_data = raw_data[self.feature_names]
        return raw_data # returns a pandas dataframe
