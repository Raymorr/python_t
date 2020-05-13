import sys
import os


from tqdm import tqdm


DEFAULT_COMPRESS_FEATURES = ['sample_data', 'acct_num_share', 'product_nm', 'mrch_country_nm',
                             'f2f_ecomm_flg', 'pos_cash_flg', 'mrch_category_01',
                             'mrch_category_02', 'mrch_category_03', 'mrch_category_04']




class FeatureCompressor(object):
    def __init__(self, folder_name=None):
        self.features = []
        if folder_name is not None:
            self._load_from_folder(folder_name)

    def add_feature_value(self, feature, value):
        if hasattr(self, feature):
            if value not in getattr(self, feature + '_id'):
                getattr(self, feature + '_id')[value] = len(getattr(self, feature))
                getattr(self, feature).append(value)
                
        else:
            self.features.append(feature)
            setattr(self, feature, [value])
            setattr(self, feature + '_id', {value: 0})

    def save_to_folder(self, folder_name):
        for feature in self.features:
            feature_filename = os.path.join(folder_name, feature + '.txt')
            with open(feature_filename, 'w') as feature_file:
                for index in range(len(getattr(self, feature))):
                    feature_file.write('{}\t{}\n'.format(index, getattr(self, feature)[index]))

    def _load_from_folder(self, folder_name):
        for filename in os.listdir(folder_name):
            if filename.endswith(".txt"):
                feature_name = filename[:-4]
                file_path = os.path.join(folder_name, filename)
                with open(file_path) as feature_file:
                    for line in feature_file:
                        line = line.strip().split('\t')
                        if len(line) == 2:
                            self.add_feature_value(feature_name, line[1])


def get_feature_compressor(filename, features_to_compress):
    feature_compressor = FeatureCompressor()

    with open(filename) as dataset_file:
        features = dataset_file.readline().strip().split('\t')
        for line in tqdm(dataset_file):
         #   print(line)
            values = line.strip().split('\t')
            for feature_name, feature_value in zip(features, values):
                if feature_name in features_to_compress:
                    feature_compressor.add_feature_value(feature_name, feature_value)
    
    return feature_compressor


def compress_dataset(filename, folder, features_to_compress=DEFAULT_COMPRESS_FEATURES):
    feature_compressor = get_feature_compressor(filename, features_to_compress)


    compressed_filename = os.path.join(folder, 'compressed_all_' + filename)
    with open(filename) as dataset_file, open(compressed_filename, 'w') as compressd_file:
        features = dataset_file.readline()
        compressd_file.write(features)
        features = features.strip().split('\t')
        for line in tqdm(dataset_file):
            values = line.strip().split('\t')
            compressed_features = []
            for feature_name, feature_value in zip(features, values):
                if feature_name in features_to_compress:
                    feature_id = getattr(feature_compressor, feature_name + '_id')[feature_value]
                    compressed_features.append(str(feature_id))
                else:
                    compressed_features.append(feature_value)
            compressd_file.write('\t'.join(compressed_features))
            compressd_file.write('\n')
    
    feature_compressor.save_to_folder(folder)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('Wrong number of arguments')
        sys.exit(0)

    dataset_filename = sys.argv[1]
    folder_name = sys.argv[2]
    os.mkdir(folder_name)
    compress_dataset(dataset_filename, folder_name)
