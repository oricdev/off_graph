# coding=utf-8
# todo: go on line 158:
# prendre produit 4000286221126 avec categories de:linsen et faire ce qui suit:
# mettre à jour la base locale en prenant la dernière version de bson
#  essayer avec le produit ci-dessus et vérifier que plusieurs categories comme ici
#   http://fr.openfoodfacts.org/api/v0/produit/4000286221126.json
#   http://world-fr.openfoodfacts.org/produit/4000286221126/rote-linsen-muller-s-muhle
#
# print "prop. '%s' = %r" % (prop, a_product.dic_props[prop])
# AttributeError: 'unicode' object has no attribute 'dic_props'


# coding=utf-8
# RESOURCES TO PYMONGO API:
# please consult https://api.mongodb.org/python/current/tutorial.html
# import json

from pymongo import MongoClient


# endpoint_root = "http://127.0.0.1:28017/off-fr/products/"
# endpoint = "http://127.0.0.1:28017/off-fr/products/?filter_categories=Hot Sauces"
# repos = json.loads(requests.get(endpoint).text)
#
# print "%r" % repos
# print "%r" % repos['rows']
# print "%r" % len(repos['rows'])

# definition of objects


# test de commentaire
class DataEnv:
    """
    Environment for data. Specifies for instance the set of fields for matching
    products to retrieve from the server (Querier)
    """
    def __init__(self, set_of_properties):
        """
        :type set_of_properties: [] of properties
        """
        # _id a dn code must be there!
        if not ("code" in set_of_properties):
            set_of_properties.insert(0, "code")
        if not ("_id" in set_of_properties):
            set_of_properties.insert(0, "_id")
        self.prod_props_to_display = set_of_properties


class Querier:
    """
    MongoClient Querier
    """

    def __init__(self, data_env, verbose):
        """
        :param verbose: True for verbosity of the Querier
        :return:  nothing
        """
        assert isinstance(data_env, DataEnv)
        self.data_env = data_env
        self.verbose = verbose
        print "verbose = %r" % verbose
        self.pongo = None
        self.db = None
        self.coll_products = None

    def connect(self):
        """
        Connection to the OFF-Product database
        :return:
        """
        if self.verbose:
            print '.. connecting to server MongoClient ("127.0.0.1", 27017)'
        self.pongo = MongoClient("127.0.0.1", 27017)
        if self.verbose:
            print ".. connecting to OPENFOODFACTS database"
        self.db = self.pongo["off-fr"]
        if self.verbose:
            print ".. getting PRODUCTS collection"
        self.coll_products = self.db["products"]
        if self.verbose:
            print "%d products are referenced" % (self.coll_products.find().count())

    def disconnect(self):
        """
        Closing connection
        :return:
        """
        if self.verbose:
            print ".. closing connection"
        self.pongo.close()
        if self.verbose:
            print "done."

    def fetch(self, prop, val):
        """
        Fecthes all products matching a single criterium
        :param prop: criterium key
        :param val: criterium value
        :return: list of Product
        """
        products_fetched = []
        # preparing projection fields for the find request (no _id)
        fields_projection = {}
        for a_prop in self.data_env.prod_props_to_display:
            fields_projection[a_prop] = 1
        # id, code and categories always retrieved
        fields_projection["_id"] = 1
        fields_projection["code"] = 1
        fields_projection["categories_tags"] = 1
        # todo: remove print "projection on %r" % fields_projection
        if self.verbose:
            print ".. fetching product details with { %s: %r } .." % (prop, val)
        products_json = self.coll_products.find({
            prop: val
        }, fields_projection)
        if products_json.count() > 0:
            for product_json in products_json:
                products_fetched.append(Product(product_json))

        return products_fetched

    def find_match(self, a_product, properties_to_match):
        """
        Perform a find for each watched crtiterium in aProduct
        :param properties_to_match: property-set for finding matching products
        :param a_product:  product with watched criteria
        :return: list of unique products matching the watched criteria of the aProduct
        """
        assert isinstance(a_product, Product)
        tmp_matching_products = {}  # dictionary in order to avoid duplicates
        _id_prod_ref = a_product.get_id()
        for criterium in properties_to_match:
            for crit_value in a_product.dic_props[criterium]:
                prods = self.fetch(criterium, crit_value)
                if self.verbose:
                    print "\t %s \t\t found %d" % (crit_value, len(prods))
                # add matching products (no duplicate since we are using a dictionary)
                for prod in prods:
                    assert isinstance(prod, Product)
                    # removing identity product / add product
                    _id_prod = prod.get_id()
                    if (_id_prod != _id_prod_ref) and not (_id_prod in tmp_matching_products):
                        tmp_matching_products[_id_prod] = prod

        # build a simple list from the temporary dictionary and return it
        matching_products = list(tmp_matching_products.values())

        return matching_products


class Statistics:
    """
    Handle statistics:
    - gather and prepare data to show
    - build graph
    """

    def __init__(self, stats_props):
        self.statsProps = stats_props

    @staticmethod
    def prepare_data(product_ref, product_others):
        """
        Prepare data before building the graph:
        - check units for extracted properties are the same. If not, perform a conversion
        :param product_ref: reference product to compare with the set of other products
        :param product_others: set of products to be compared statistically with the reference product
        :return:
        """
        assert isinstance(product_ref, Product)
        assert isinstance(product_others, Product[:])
        # todo: code

        return None


class Gui:
    """
    Gui Object
    """

    def __init__(self, data_env):
        assert isinstance(data_env, DataEnv)
        self.data_env = data_env

    def display(self, a_product):
        """
        Display all properties of the product if prop_to_display not set
        :param a_product: product for which we want to display the properties and their values
        """
        assert isinstance(a_product, Product)
        if len(self.data_env.prod_props_to_display) == 0:
            props_to_show = a_product.dic_props
        else:
            props_to_show = self.data_env.prod_props_to_display
        print "LISTING of %d properties::" % len(props_to_show)
        for prop in props_to_show:
            print 'prop. \'%s\' = %r' % (prop, a_product.dic_props[prop])


class Product:
    def __init__(self, properties):
        self.dic_props = properties
        self.prop_to_display = None
        # todo: remove print "creating product with properties = %r" % properties

    def get_id(self):
        return self.dic_props["_id"]

    def calc_proximity(self, product_ref):
        """
        The bigger the intersection of categories between self and product_ref, the closer
        Note: if intersection is 100%, then proximity is 0
        :rtype: None
        :param product_ref:
        :return:
        """
        assert isinstance(product_ref, Product)
        nb_categs_self = len(self.dic_props["categories_tags"])
        nb_categs_ref = len(product_ref.dic_props["categories_tags"])
        # todo: ratio à utiliser!
        # todo: voir le cas où une seule catégorie (plus generalement où nb categs self = nb categs produitRéférent)

# initialize: Data Environment, Gui for display, and Querier
data_env1 = DataEnv(["code", "generic_name", "countries_tags", "categories_tags", "nutriments", "allergens"])
gui = Gui(data_env1)
querier = Querier(data_env1, True)

# connecting to server
querier.connect()

# input product code
# ex.: 0001120209
# ex.: 3017620429484
print
prod_code = raw_input("please enter a product code ['q'uit] > ")

while prod_code != "q":
    if prod_code == "":
        prod_code = "3017620429484"
        print ".. fetching default product with code '%s'" % prod_code

    # retrieve product details into object
    products = querier.fetch("code", prod_code)
    print ".. number of products found:", len(products)

    if len(products) == 0:
        print "WARNING: the product with code '%s' could not be found!" % prod_code
    else:
        if len(products) > 1:
            print "WARNING: more than 1 product match ... choosing 1st product"

        # todo: perfectionner avec ces multi-criteres (ci-dessous)
        # .. myProduct = Product(data_products[0], ["countries", "categories"], ["nutriments", "allergens"])
        myProduct = products[0]
        assert isinstance(myProduct, Product)
        gui.display(myProduct)

        # fetch similar products with the same categories
        props_to_match = [
            "categories_tags"]  # for the search of similar products based on this set of properties (matching criteria)
        products_match = querier.find_match(myProduct, props_to_match)
        print ".. NUMBER of matching distinct products found: %d" % len(products_match)

        print ".. calculating proximity of all matching products with your product.."
        for product in products_match:
            product.calc_proximity(myProduct)

        # todo: plus tard
        statsProps = [
            "nutriments"]  # for all products, extracting of these specific items for building the statistical graphs

    print
    prod_code = raw_input("please enter a product code ['q'uit] > ")
# extract categories and nutriments

# retrieve related products for each related category

# make unique products

# extract nutriments of the retrieved set of products

# analysis required on a few samples

# closing connection
querier.disconnect()
