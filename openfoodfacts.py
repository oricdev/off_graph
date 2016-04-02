# coding=utf-8
# todo:
# todo: ** brand dans les mini_product + url_product + url_img
# todo: ** algorithme de répartition homogène des points: le tester sur pretit exemple, puis ici

# 1)
# prendre produit 4000286221126 avec categories de:linsen et faire ce qui suit:
# mettre à jour la base locale en prenant la dernière version de bson
#  essayer avec le produit ci-dessus et vérifier que plusieurs categories comme ici
#   http://fr.openfoodfacts.org/api/v0/produit/4000286221126.json
#   http://world-fr.openfoodfacts.org/produit/4000286221126/rote-linsen-muller-s-muhle
#
# 2)
# essayer avec produit 3256220450034 (boissons et beverages, plus de 10.000 références en tout!)
#   categAliments et boissons à base de végétaux ==> 10.000 produits

# print "prop. '%s' = %r" % (prop, a_product.dic_props[prop])
# AttributeError: 'unicode' object has no attribute 'dic_props'


# coding=utf-8
# RESOURCES TO PYMONGO API:
# please consult https://api.mongodb.org/python/current/tutorial.html
# import json
from __future__ import division
from collections import Counter
from pymongo import MongoClient
import matplotlib.pyplot as plt


# endpoint_root = "http://127.0.0.1:28017/off-fr/products/"
# endpoint = "http://127.0.0.1:28017/off-fr/products/?filter_categories=Hot Sauces"
# repos = json.loads(requests.get(endpoint).text)
#
# print "%r" % repos
# print "%r" % repos['rows']
# print "%r" % len(repos['rows'])

# definition of objects
# from sympy.galgebra.ncutil import product_derivation


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
        Perform a find for each watched criterion in aProduct
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
                    if _id_prod != _id_prod_ref:
                        if not (_id_prod in tmp_matching_products):
                            tmp_matching_products[_id_prod] = prod
                        else:
                            assert isinstance(tmp_matching_products[_id_prod], Product)
                            tmp_matching_products[_id_prod].incr_intersection_with_ref()

        # build a simple list from the temporary dictionary and return it
        matching_products = list(tmp_matching_products.values())

        return matching_products


class Graph:
    """
    Handle statistics:
    - gather and prepare data to show
    - build graph
    """

    def __init__(self, stats_props, product_ref, products_others, verbose):
        assert isinstance(product_ref, Product)

        self.verbose = verbose
        self.statsProps = stats_props
        self.product_ref = product_ref
        self.xaxis_prod_ref = []
        self.yaxis_prod_ref = []
        self.products_matching = products_others
        # Graph uses its own data set which is a conversion of products_matching
        self.data_set_ref = []
        self.data_set_others = []
        self.xaxis_others = []
        self.yaxis_others = []

    def show(self):
        self.prepare_data()
        self.prepare_graph()

        plt.show()

    def prepare_data(self):
        # todo:
        if self.verbose:
            print ".. preparing the data for the show"

        # preparing product reference
        mini_prod = {"code": self.product_ref.dic_props["code"],
                     "generic_name": self.product_ref.dic_props["generic_name"],
                     # todo
                     "brand": "",
                     "url_product": "",
                     "url_img": "",
                     "score_proximity": self.product_ref.score_proximity,
                     "score_nutrition": self.product_ref.score_nutrition,
                     "x_val_real": self.product_ref.score_proximity,
                     "y_val_real": self.convert_scoreval_to_note(self.product_ref.score_nutrition),
                     "x_val_graph": self.product_ref.score_proximity,
                     "y_val_graph": self.convert_scoreval_to_note(self.product_ref.score_nutrition)
                     }
        self.data_set_ref.append(mini_prod)

        for product in products_match:
            mini_prod = {"code": product.dic_props["code"], "generic_name": product.dic_props["generic_name"],
                         # todo
                         "brand": "",
                         "url_product": "",
                         "url_img": ""}
            product.compute_scores(self.product_ref)
            mini_prod["score_proximity"] = product.score_proximity
            mini_prod["score_nutrition"] = product.score_nutrition
            mini_prod["x_val_real"] = product.score_proximity
            mini_prod["y_val_real"] = self.convert_scoreval_to_note(product.score_nutrition)
            # todo: will be converted later on (below)
            mini_prod["x_val_graph"] = mini_prod["x_val_real"]
            mini_prod["y_val_graph"] = mini_prod["y_val_real"]
            self.data_set_others.append(mini_prod)

    def prepare_graph(self):
        """
        Prepare data before building the graph:
        - check units for extracted properties are the same. If not, perform a conversion
        :return:
        """
        # prepare for product reference
        self.xaxis_prod_ref.append(self.data_set_ref[0].pop("x_val_graph"))
        self.yaxis_prod_ref.append(self.data_set_ref[0].pop("y_val_graph"))

        # prepare for all other matching products
        for mini_prod in self.data_set_others:
            self.xaxis_others.append(mini_prod.pop("x_val_graph"))
            self.yaxis_others.append(mini_prod.pop("y_val_graph"))

        plt.plot(self.xaxis_prod_ref, self.yaxis_prod_ref, 'r-')
        plt.scatter(self.xaxis_others, self.yaxis_others)

        # verbosity details
        if self.verbose:
            print
            print "Product ref. x / y: %r ∕ %r" % (self.xaxis_prod_ref, self.yaxis_prod_ref)
            print "Matching products with COUNTER:"
            print "\t Counter(x): %r" % Counter(self.xaxis_others)
            print "\t Counter(y): %r" % Counter(self.yaxis_others)

    @staticmethod
    def uniform_repartition():
        """
        Algorithm of " Uniformly Distributed Random Points Inside a Circle (2)" here:
        http://narimanfarsad.blogspot.ch/2012/11/uniformly-distributed-points-inside.html
        :return:
        """
        pass
        # todo: implement

    def convert_scoreval_to_note(self, score_nutrition):
        # todo: distinguer Eaux et Boissons des aliments solides .. ici, que aliments solides
        # ici http://fr.openfoodfacts.org/score-nutritionnel-france
        # A - Vert : jusqu'à -1
        # B - Jaune : de 0 à 2
        # C - Orange : de 3 à 10
        # D - Rose : de 11 à 18
        # E - Rouge : 19 et plus
        if score_nutrition < 0:
            return 5  # A
        elif score_nutrition < 3:
            return 4  # B
        elif score_nutrition < 11:
            return 3  # C
        elif score_nutrition < 19:
            return 2  # D
        else:
            return 1  # E


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
            if prop in a_product.dic_props:
                print 'prop. \'%s\' = %r' % (prop, a_product.dic_props[prop])

        # additionally, show scores if available
        print "score prox. = %r" % a_product.score_proximity
        print "score nutri = %r" % a_product.score_nutrition


class Product:
    def __init__(self, properties):
        self.isRef = False
        # while fetching similar products, always 1 at creation since there was a match on a category
        self.nb_categories_intersect_with_ref = 1
        # Proximity with product reference is computed later on
        self.score_proximity = 0
        self.score_nutrition = 0
        self.dic_props = properties
        # exclude from graph if no comparison possible
        self.excludeFromGraph = False
        # todo: remove print "creating product with properties = %r" % properties

    def get_id(self):
        return self.dic_props["_id"]

    def set_as_reference(self, is_ref):
        self.isRef = is_ref
        if is_ref:
            self.score_proximity = 1
            # compute also the nutrition score
            self.calc_score_nutrition()

    def incr_intersection_with_ref(self):
        """
        When a match on category is found with product reference, then we increment the number of intersected categories
        in order to speed up a bit the proximity computation thereafter
        :return:
        """
        self.nb_categories_intersect_with_ref += 1

    def compute_scores(self, product_ref):
        self.calc_score_proximity(product_ref)
        self.calc_score_nutrition()

    def calc_score_proximity(self, product_ref):
        """
        The bigger the intersection of categories between self and product_ref, the closer
        Note: if intersection is 100%, then proximity is 100%
        Proximity = nb_categ_intersect / nb_categ_prod_ref
        :rtype: None
         :param product_ref:
         :return:
         """
        assert isinstance(product_ref, Product)
        nb_categs_ref = len(product_ref.dic_props["categories_tags"])
        self.score_proximity = self.nb_categories_intersect_with_ref / nb_categs_ref

    def calc_score_nutrition(self):
        """
        see : http://fr.openfoodfacts.org/score-nutritionnel-france
        :return:
        """
        nutriments = self.dic_props["nutriments"]
        if not ("nutrition-score-uk" in nutriments):
            # add security in case this is the product reference (we want it to be shown in the graph)
            if self.isRef:
                self.score_nutrition = 0
                self.score_proximity = 0
            else:
                self.excludeFromGraph = True
        else:
            # initialize: Data Environment, Gui for display, and Querier
            self.score_nutrition = int(nutriments["nutrition-score-uk"])


data_env1 = DataEnv(
    ["code", "generic_name", "countries_tags", "categories_tags", "nutriments", "allergens"])
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
        # Is the  product reference!
        myProduct.set_as_reference(True)
        gui.display(myProduct)

        # fetch similar products with the same categories
        props_to_match = [
            "categories_tags"]  # for the search of similar products based on this set of properties (matching criteria)
        products_match = querier.find_match(myProduct, props_to_match)
        print ".. NUMBER of matching distinct products found: %d" % len(products_match)

        # for ij in range(0, 10):
        #     print "%d" % ij
        #     gui.display(products_match[ij])
        # print "\t code: %r" % products_match[ij].dic_props["code"]
        # print "\t\t proximity: %r" % products_match[ij].score_proximity
        # print "\t\t nutriments %r" % products_match[ij].dic_props["nutriments"]["nutrition-score-uk"]

        # todo: plus tard
        statsProps = [
            "nutriments"]  # for all products, extracting of these specific items for building the statistical graphs
        g = Graph(statsProps, myProduct, products_match, True)
        g.show()

    print
    prod_code = raw_input("please enter a product code ['q'uit] > ")
# extract categories and nutriments

# retrieve related products for each related category

# make unique products

# extract nutriments of the retrieved set of products

# analysis required on a few samples

# closing connection
querier.disconnect()
