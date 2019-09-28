import pandas as pd
import re
import json
from fuzzywuzzy import fuzz
from geopy.geocoders import Nominatim
from haversine import haversine


def process_bedroom(input):
    '''
    function to process column bedroom, which will be used in apply function later.
    :param input: bedroom column value
    :return: clean value
    '''
    input = re.findall(r'[\d\+]+', input)
    if input == []:
        return None
    else:
        value = input[0]
        if '+' not in value:
            return int(value)
        else:
            if value[-1] == '+':
                value += '0'
            return eval(value)


def area_fill(area, land):
    if pd.isnull(area):
        return land
    else:
        return area


def price_per_sqft(psf, price, area):
    if pd.notnull(psf):
        return psf
    else:
        if pd.notnull(price) and pd.notnull(area):
            return price / area
        else:
            return None


def clean_data(data):
    '''
    function to clean the whole scraped data, first process each columns and then remove rows with null value.
    :param data: the raw data.
    :return: the clean data.
    '''
    type_set = {
        'condominium',
        'apartment',
        'hdb',
        'bungalow',
        'terrace house',
    }

    for col in data.columns:
        if '_dist' in col or col == 'psf':
            data[col] = data[col].str.extract('([\d\.]+)', expand=True).astype(float)

    data['type'] = data['type'].str.replace('type: ', '')
    data = data[data['type'].isin(type_set)]
    data['tenure'] = data['tenure'].str.replace('freehold', '10000')
    data['tenure'] = data['tenure'].str.extract('(\d+)', expand=True).astype(float)
    data['price'] = data['price'].str.extract('([\d,]+)', expand=True)
    data['price'] = data['price'].str.replace(',', '').astype(float)
    data['latlon'] = data['latlon'].str.extract('(=[\d,\.]+)', expand=True)
    data['lat'], data['lon'] = zip(*data['latlon'].str.replace('=','').str.split(','))
    data['lat'] = data['lat'].astype(float)
    data['lon'] = data['lon'].astype(float)
    data['bedroom'] = data['bedroom'].apply(process_bedroom)
    data['area'] = data[['area', 'land']].apply(lambda x: area_fill(*x), axis=1)
    data['area'] = data['area'].str.extract('([\d,]+)', expand=True)
    data['area'] = data['area'].str.replace(',', '').astype(float)
    data['psf'] = data[['psf', 'price', 'area']].apply(lambda x: price_per_sqft(*x), axis=1)
    data['address'] = data['address'].str.replace('address: ', '')

    data = data.drop(['title', 'land', 'description', 'condition', 'code', 'bathroom', 'latlon'], axis=1)
    data = data.dropna(subset=['price', 'district'])

    return data


def geo_locate(file_name):
    '''
    to read geo location information from geojson files downloaded from data.gov.sg
    :param file_name: file_name
    :return: a list of geo locations
    '''
    locations = []
    with open(file_name) as f:
        geo = json.loads(f.read())

    for i in geo['features']:
        lon, lat, _ = i['geometry']['coordinates']
        locations.append((lat, lon))

    return locations


def read_mrt_info(file_name):
    mrt = pd.read_csv(file_name)
    mrt = mrt[mrt['COLOR'] != 'OTHERS']
    mrt = pd.concat([mrt, pd.get_dummies(mrt['COLOR'])],axis=1)
    mrt = mrt.groupby('STN_NAME').max()
    mrt = mrt[['BLUE', 'GREEN', 'PURPLE', 'RED', 'YELLOW', 'COLOR']]
    mrt = mrt.reset_index()
    mrt['count'] = mrt.sum(axis=1)
    mrt['COLOR'][mrt['count'] > 1] = 'MULTI'
    mrt = mrt.rename(columns={'COLOR': 'nearest_mrt_color'})

    return mrt


def find_most_similar(origin_list, compare_list):
    '''
    function to find the most similiar items from the compare list for each of the item
    in the original list
    :param origin_list: the item to find reference from
    :param compare_list: the reference list
    :return: a list that contains the (original item, most_similar_item, match_score)
    '''
    output = []
    for org_item in origin_list:
        matched = None
        max_score = None
        for compare_item in list(compare_list):
            score = fuzz.ratio(str(org_item).lower(), str(compare_item).lower())
            if max_score is None:
                max_score = score
                matched = compare_item
            else:
                if score > max_score:
                    max_score = score
                    matched = compare_item

        output.append((org_item, matched, max_score))

    return output


def get_primary_school_map(data):
    '''
    map primary school name to its admission rate and score
    :return: dataframe of school name mapping
    '''
    schools = set(data['first_p_school']) | set(data['sec_p_school']) | set(data['third_p_school'])
    p_school_ranking = pd.read_excel('extra_info.xlsx', sheet_name='primary school')
    similar_p_schools = find_most_similar(schools, list(p_school_ranking['primary_school']))
    sim_data = pd.DataFrame(similar_p_schools, columns=['p_school_name', 'primary_school', 'score'])
    sim_data = sim_data.merge(p_school_ranking, on='primary_school', how='left')
    sim_data = sim_data.drop(['primary_school', 'score'],axis=1)

    return sim_data


def get_mrt_map(data):
    '''
    map mrt name to its number of lines and which line it belongs to
    :return: dataframe of mrt mapping
    '''
    origin_mrts = set(data['first_mrt_name']) | set(data['sec_mrt_name']) | set(data['third_mrt_name'])
    mrt = read_mrt_info('mrtsg.csv')

    similar_mrts = find_most_similar(origin_mrts, list(mrt['STN_NAME']))
    sim_data = pd.DataFrame(similar_mrts, columns=['mrt_name', 'STN_NAME', 'score'])
    sim_data = sim_data.merge(mrt, on='STN_NAME', how='left')
    sim_data = sim_data.drop(['STN_NAME', 'score'], axis=1)

    return sim_data


def geolocate_shops():
    '''
    function to call geopy api to get geolocation information for a list of shops
    :return: the list of shopping mall (lat, lon).
    '''
    osm = Nominatim()
    shops = pd.read_excel('extra_info.xlsx', sheet_name='shops')

    output = []
    for i in shops['shopping_mall']:
        mall = osm.geocode(i + ', Singapore')
        if mall is not None:
            output.append((mall.latitude, mall.longitude))
        else:
            output.append((None, None))


def get_shop_locations():
    shops = pd.read_excel('extra_info.xlsx', sheet_name='shops')
    shop_locs = [(row['lat'], row['lon']) for _, row in shops.iterrows()]
    return shop_locs


def get_international_school_map(data):
    '''
    map international school name to whether its in top 20 or not
    :return: dataframe of school name mapping
    '''
    schools = set(data['first_i_school']) | set(data['sec_i_school']) | set(data['third_i_school'])
    top_i_schools = pd.read_excel('extra_info.xlsx', sheet_name='international school')
    top_i_schools = set(top_i_schools['mapped'])

    output = pd.DataFrame(list(schools), columns = ['international_school'])
    output['in_top_20'] = output['international_school'].apply(lambda x: True if x in top_i_schools else False)

    return output


def nearest_dist(lat, lon, point_list):
    '''
    find shortest distance to a certain amenity (shops, food courts or supermarkets) of the house
    :param lat: latitude of the house
    :param lon: longitude of the house
    :param point_list: the (lat, lon) list of the amenities
    :return: the shortest distance
    '''
    origin = (lat, lon)
    dist_list = [haversine(origin, point) for point in point_list]
    return min(dist_list)


def data_engineering(data):
    '''
    function to conduct data engineering on the clean data
    :param data: the clean data
    :return: two dataframes, the data for analysis and data for building models.
    '''
    txt_cols = [
        'address',
        'first_i_school',
        'sec_i_school',
        'third_i_school',
        'first_p_school',
        'sec_p_school',
        'third_p_school',
        'first_mrt_name',
        'sec_mrt_name',
        'third_mrt_name',
        'road',
    ]
    downtown_loc = [(1.279455, 103.852814)]
    supermarket_locs = geo_locate('supermarkets-geojson.geojson')
    foodcourt_locs = geo_locate('hawker-centres-geojson.geojson')
    primary_school = get_primary_school_map(data)
    international_school = get_international_school_map(data)
    shop_locs = get_shop_locations()
    mrt = get_mrt_map(data)

    p_school_dist_cols = ['first_p_school_dist', 'sec_p_school_dist', 'third_p_school_dist']
    data['num_p_school_in_1km'] = data[p_school_dist_cols].apply(lambda x: x <= 1).sum(axis=1)
    i_school_dist_cols = ['first_i_school_dist', 'sec_i_school_dist', 'third_i_school_dist']
    data['num_i_school_in_1km'] = data[i_school_dist_cols].apply(lambda x: x <= 1).sum(axis=1)
    mrt_dist_cols = ['first_mrt_dist', 'sec_mrt_dist', 'third_mrt_dist']
    data['num_mrt_in_1km'] = data[mrt_dist_cols].apply(lambda x: x <= 1).sum(axis=1)

    data = data.merge(primary_school, how='left', left_on='first_p_school', right_on='p_school_name')
    data = data.merge(international_school, how='left', left_on='first_i_school', right_on='international_school')
    data = data.merge(mrt, how='left', left_on='first_mrt_name', right_on='mrt_name')

    dist_to_shops = lambda x, y: nearest_dist(lat=x, lon=y, point_list=shop_locs)
    data['dist_to_shops'] = data[['lat', 'lon']].apply(lambda x: dist_to_shops(*x), axis=1)
    dist_to_foodcourts = lambda x, y: nearest_dist(lat=x, lon=y, point_list=foodcourt_locs)
    data['dist_to_foodcourt'] = data[['lat', 'lon']].apply(lambda x: dist_to_foodcourts(*x), axis=1)
    dist_to_supermarket = lambda x, y: nearest_dist(lat=x, lon=y, point_list=supermarket_locs)
    data['dist_to_supermarket'] = data[['lat', 'lon']].apply(lambda x: dist_to_supermarket(*x), axis=1)
    dist_to_downtown = lambda x, y: nearest_dist(lat=x, lon=y, point_list=downtown_loc)
    data['dist_to_downtown'] = data[['lat', 'lon']].apply(lambda x: dist_to_downtown(*x), axis=1)

    data = data.drop(['international_school', 'p_school_name', 'mrt_name'], axis=1)

    model_data = data.drop(txt_cols, axis=1)
    type_dummy = pd.get_dummies(model_data['type'])
    type_dummy = type_dummy.rename(columns={'terrace house': 'terrace_house'})
    model_data = pd.concat([model_data, type_dummy], axis=1)
    model_data = model_data.drop(['district', 'type', 'tenure', 'nearest_mrt_color'], axis=1)
    model_data = model_data.dropna()

    return data, model_data


if __name__ == '__main__':

    data = pd.read_csv("scraped_data.csv")
    data = clean_data(data)
    data, model_data = data_engineering(data)
    data.to_csv('engineered_data.csv', index=False)
    model_data.to_csv('model_data.csv', index=False)

