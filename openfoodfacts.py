# coding=utf-8
from __future__ import division
from collections import Counter
from pymongo import MongoClient
import matplotlib.pyplot as plt
import matplotlib.colors
import mpld3

from numpy import pi
import numpy
from os.path import expanduser


# The algorithm below is strongly inspired from the one available here:
# http://stackoverflow.com/questions/5408276/sampling-uniformly-distributed-random-points-inside-a-spherical-volume
# This is here a repartition on a disk instead on a sphere (1 angle required and 2 coordinates)
class PointRepartition:
    def __init__(self, nb_particles):
        self.number_of_particles = nb_particles

    def new_positions_spherical_coordinates(self):
        """
        Sample of returns:
        x = array([[-0.01886142], [-0.04094547], [-0.53896705]]) //
        y = array([[-0.11048884], [-0.42567348], [ 0.557865  ]])
        :return:
        """
        radius = numpy.random.uniform(0.0, 1.0, (self.number_of_particles, 1))
        theta = numpy.random.uniform(-1., 1., (self.number_of_particles, 1)) * pi
        x = radius * numpy.sin(theta)
        y = radius * numpy.cos(theta)
        return x, y


class DataEnv:
    """
    Environment for data. Specifies the set of fields retrieved from server for matching
    products (Querier)
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
        # todo: review since hard-coded!
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
        # id, code and categories always retrieved (used as filter criteria = projection)
        fields_projection["_id"] = 1
        fields_projection["code"] = 1
        fields_projection["categories_tags"] = 1

        if self.verbose:
            print ".. fetching product details with { %s: %r } .." % (prop, val)

        products_json = self.coll_products.find({
            prop: val
        }, fields_projection)
        if products_json.count() > 0:
            for product_json in products_json:
                products_fetched.append(Product(product_json))

        # todo: change the number of returned products
        return products_fetched[0:100]
        # return products_fetched

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
        # x, y coordinates on the graph and label to display for the product reference
        self.xaxis_prod_ref_real = []
        self.yaxis_prod_ref_real = []
        self.label_prod_ref = []

        self.products_matching = products_others
        # x, y coordinates on the graph and label to display for all matching products
        self.xaxis_others_real = []
        self.yaxis_others_real = []
        self.labels_others = []

        # print "length is %d" % len(self.products_matching)
        # Graph uses its own data set which is a conversion of products_matching: preparation of these datasets
        self.data_set_ref = []
        self.data_set_others = []
        self.xaxis_others_distributed = []
        self.yaxis_others_distributed = []
        # todo: use this one d3 for d3.js Page!
        self.d3_json = []

    def show(self):
        self.prepare_data()
        self.prepare_graph()

        # plt.show()

    def prepare_data(self):
        if self.verbose:
            print ".. preparing the data for the show"

        # preparing product reference
        mini_prod = {"code": self.product_ref.dic_props["code"],
                     "generic_name": self.product_ref.dic_props["generic_name"],
                     # todo
                     "brands_tags": self.product_ref.dic_props["brands_tags"],
                     "url_product": "",
                     "url_img": "",
                     "lc": self.product_ref.dic_props["lc"],
                     "images": self.product_ref.dic_props["images"],
                     "score_proximity": self.product_ref.score_proximity,
                     "score_nutrition": self.product_ref.score_nutrition,
                     "x_val_real": self.product_ref.score_proximity,
                     "y_val_real": self.convert_scoreval_to_note(self.product_ref.score_nutrition)
                     # ,
                     # "x_val_graph": self.product_ref.score_proximity,
                     # "y_val_graph": self.convert_scoreval_to_note(self.product_ref.score_nutrition)
                     }
        self.data_set_ref.append(mini_prod)

        # preparing data for all other matching products
        for product in self.products_matching:
            mini_prod = {"code": product.dic_props["code"], "generic_name": product.dic_props["generic_name"],
                         # todo
                         "brands_tags": product.dic_props["brands_tags"],
                         "url_product": "",
                         "url_img": "",
                         "lc": self.product_ref.dic_props["lc"],
                         "images": self.product_ref.dic_props["images"]
                         }
            product.compute_scores(self.product_ref)
            mini_prod["score_proximity"] = product.score_proximity
            mini_prod["score_nutrition"] = product.score_nutrition
            mini_prod["x_val_real"] = product.score_proximity
            mini_prod["y_val_real"] = self.convert_scoreval_to_note(product.score_nutrition)
            self.xaxis_others_real.append(mini_prod["x_val_real"])
            self.yaxis_others_real.append(mini_prod["y_val_real"])
            self.data_set_others.append(mini_prod)

    def prepare_graph(self):
        """
        Prepare data before building the graph:
        - check that units for extracted properties are the same. If not, perform a conversion
        Algorithm of " Uniformly Distributed Random Points Inside a Circle (2)" here:
        http://narimanfarsad.blogspot.ch/2012/11/uniformly-distributed-points-inside.html
        :return:
        """
        # todo: ugly code: to be deeply reviewed
        # prepare for product reference
        nb_categs_ref = len(self.product_ref.dic_props["categories_tags"])
        self.xaxis_prod_ref_real.append(nb_categs_ref * self.data_set_ref[0]["x_val_real"])
        self.yaxis_prod_ref_real.append(self.data_set_ref[0]["y_val_real"])
        label_prod_ref = self.data_set_ref[0]["code"]
        self.label_prod_ref.append(label_prod_ref)

        # prepare for all other matching products
        # .. using a uniform repartition
        sample = PointRepartition(len(self.data_set_others))
        x, y = sample.new_positions_spherical_coordinates()
        # print "x = %r // y = %r" % (x, y)
        v_x = []
        v_y = []
        for x0, y0 in zip(x, y):
            # print "%r // %r " % (x0[0], y0[0])
            v_x.append(x0[0])
            v_y.append(y0[0])

        for mini_prod, x0, y0 in zip(self.data_set_others, v_x, v_y):
            x, y = mini_prod["x_val_real"], mini_prod["y_val_real"]
            # print "miniprod = %d, %d" % (x, y)
            # NOTE: since we display 2 graphs (1 for all points, and 1 for the coloured stripes with a specific design
            #  for the CELL matching the product reference, we need to extend the x Values (mult. by nb categs
            #  of product reference)
            x_coord = nb_categs_ref * (x - (
                1 / (2 * nb_categs_ref) * (1 - x0)))
            y_coord = y - (
                0.5 * (1 - y0))
            # print "computed for display = %d, %d" % (x_dspl, y_dspl)

            self.xaxis_others_distributed.append(x_coord)
            self.yaxis_others_distributed.append(y_coord)
            print "code product = %r " % mini_prod["code"]
            if mini_prod["code"] == "0028000682309":
                print "stop"
            url_prod = "http://fr.openfoodfacts.org/produit/" + mini_prod["code"]
            url_img = "http://static.openfoodfacts.org/images/products/" + mini_prod["code"][0:3]+"/" \
                      + mini_prod["code"][3:6] \
                      + "/" + mini_prod["code"][6:9]+"/"+mini_prod["code"][9:]+"/front_" \
                      + mini_prod["lc"] + "." + mini_prod["images"][u"front"][u"rev"] + ".400.jpg"
            print "img url = %r " % url_img
            the_label = "<div style='background-color: #ffffff'><a href='http://world.openfoodfacts.org/product/" \
                        + mini_prod["code"] + "'>" \
                        + mini_prod["code"] + " / " + " // ".join(mini_prod["brands_tags"]) + " / " \
                        + mini_prod["generic_name"] + "<br/>" \
                        + "<img src='" + url_img + "' height = '200px' />" \
                        + "</a><br/></div>"
            self.labels_others.append(url_prod)
            self.labels_others.append(the_label)
            self.d3_json.append({"x": x_coord, "y": y_coord, "url": url_prod, "content": the_label})

        nb_rows = 5  # nb of rows
        # make an empty data set
        data = numpy.ones((nb_rows, nb_categs_ref)) * numpy.nan

        # data[0:1, 0] = 5
        # data[0:1, 1] = 4
        # data[0:1, 2] = 3
        # data[0:1, 3] = 2
        # data[0:1, 4] = 1

        # Associate values to nutrition scores A to E (on the whole row)
        data[0,] = 1
        data[1,] = 2
        data[2,] = 3
        data[3,] = 4
        data[4,] = 5
        # Set background color for the product reference
        # print self.yaxis_prod_ref_real
        data[self.yaxis_prod_ref_real[0] - 1, nb_categs_ref - 1] = numpy.nan

        # make a figure + axes
        fig, ax = plt.subplots(1, 1, tight_layout=True)
        # make nutrition score coloured stripes
        # todo: alpha 0.3 required, except for the cell matching the product reference (alpha = 1)
        my_cmap = matplotlib.colors.ListedColormap(['#ff0000', '#ff0180', '#ff6701', '#ffff00', '#00ff00'])
        # set the 'bad' values (nan) to be white and transparent
        my_cmap.set_bad(alpha=0)
        # draw the grid
        # for x in range(0, 1):
        #     ax.axhline(x, lw=2, color='k', zorder=5, alpha=0.2)
        #     ax.axvline(x, lw=2, color='k', zorder=5, alpha=0.2)

        ax.set_title("Nutrition scores for products similar to your selected product [" + self.label_prod_ref[0] + "]",
                     size=12)
        ax.set_alpha(0.2)
        # draw the boxes
        ax.imshow(data, interpolation='none', cmap=my_cmap, extent=[0, nb_categs_ref, 0, nb_rows], zorder=0)
        # ax.imshow(data, interpolation='none', cmap=my_cmap, zorder=0)

        plt.xticks(numpy.arange(0, nb_categs_ref + 0.1, 1),
                   ('low match',) + tuple('' for _ in range(1, nb_categs_ref)) + ('full match',))
        plt.yticks(numpy.arange(0, 6, 1.0), ('', 'E', 'D', 'C', 'B', 'A'))
        # todo: remove spot current product .. scatter_ref = plt.scatter(self.xaxis_prod_ref_real,
        # todo: self.yaxis_prod_ref_real, color='#000000')
        scatter_others = plt.scatter(self.xaxis_others_distributed, self.yaxis_others_distributed)
        tooltip = mpld3.plugins.PointHTMLTooltip(scatter_others, labels=self.labels_others)
        mpld3.plugins.connect(fig, tooltip)
        home = expanduser("~")
        mpld3.save_html(fig, home + "/prod_" + str(self.label_prod_ref[0]) + ".html")
        # todo: issue with ticks in mpld3 (not available yet):
        # cf. http://stackoverflow.com/questions/35446525/setting-tick-labels-in-mpld3

        # verbosity details
        # if self.verbose:
        print
        print "Product ref. x / y: %r ∕ %r" % (self.xaxis_prod_ref_real, self.yaxis_prod_ref_real)
        print "Matching products with COUNTER:"
        print "\t Counter(x): %r" % Counter(self.xaxis_others_real)
        print "\t x = %r", self.xaxis_others_distributed
        print "\t Counter(y): %r" % Counter(self.yaxis_others_real)
        print "\t y = %r", self.yaxis_others_distributed
        print
        print " json for d3 object = %r" % self.d3_json

        # !! Activate either mpld3.show or plt.show !!
        mpld3.show()
        # todo: attention -> behaviour is a bit different to mpld3 and currently wrong:
        # todo: .. the white square is currently shown mirrored in comparison with mpld3, which is wrong
        plt.show()

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
        print "score proximity with ref. product = %r" % a_product.score_proximity
        print "score nutritional = %r" % a_product.score_nutrition


class Product:
    def __init__(self, properties):
        # product reference (no by default)
        self.isRef = False
        # Nb of categories' intersections with reference product:
        # while fetching similar products, always 1 at creation since there was a match on a category
        self.nb_categories_intersect_with_ref = 1
        # Proximity with product reference is computed later on
        self.score_proximity = 0  # X-axis
        self.score_nutrition = 0  # Y-axis
        self.dic_props = properties
        # exclude from graph if no comparison possible.
        # We can add exclusion criteria such as:
        #  * generic-name is empty
        #  * too far in similarity with reference product (nb categories intersections too low)
        self.excludeFromGraph = False

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
            # todo: to be reviewed for waters, countries, etc., as explained in the above url
            # initialize: Data Environment, Gui for display, and Querier
            self.score_nutrition = int(nutriments["nutrition-score-uk"])


# ##########################
# ENTRY POINT FOR THE CODE #
# ##########################

# lc and images->front->rev are used for building the path to the picture of the product
data_env1 = DataEnv(
    ["code", "generic_name", "countries_tags", "categories_tags", "nutriments", "allergens", "brands_tags", "lc", "images"])
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
