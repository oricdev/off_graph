Feel free to contact me on my email if you encounter any problem for setup or have any question related to this application.
<br/>
<h1>Purpose</h1>
This application is in a draft version and is bound to the openfoodfacts.org application.
<br/>
It runs currently in a console mode, but displays its results as a graph on localhost (web display).
<br/>
After having entered a product reference (in the same way as in <i>www.openfoodfacts.org</i>), it will seek for similar products in the OFF database and display them on a graph based on their nutrition-score (grades A to E) and their similarity with the product reference.
<br/>
It makes it then possible to the consumer to look for more or less similar products with better nutrition properties if wanted.

<h1>Requirements</h1>
Proceed first with the setup described here: http://openfoodfacts.github.io/OpenFoodFacts-APIRestPython/

<h1>How it works?</h1>
Once you have entered a product reference in the command line, the application fetches a subset of information for this product, and especially the <i>nutriments</i> (for computing the nutrition score) and the <it>categories_tags</it> (for fetching more or less similar products).
<br/>
The application then fetches in the database all products for each entry of the <i>categories_tags</i> which the reference product belongs to (this is surely not optimal!). The intersection of the categories_tags for fetched products and the reference product is computed. The higher the intersection, the closer the similarity with the reference product; so for now, the "score proximity" of a product with the reference product is computed as follows:
<br/><br/>
<i>&lt;nb of intersected categories_tags of product X &gt; / &lt;nb of categories_tags of reference product&gt;</i>
<br/><br/>
Note: if all categories_tags of the reference product are listed in another product, then the match is 1, i.e. 100%

<h1>How to start</h1>
Once the OFF database is decompacted (see "Requirements" above), perform the following actions:
<br/>
- start the mongo server locally in a terminal with appropriate options (ex.: <i>mongod --httpinterface --rest --dbpath ./db_produits/dump/off-fr/ </i>). Wenn the server tells the following, then the connection is ok:
    [initandlisten] waiting for connections on port 27017
    [websvr] admin web console waiting for connections on port 28017
- before running the application, you may need to update the hard-coded localhost call: locate the Class "Querier"/method "connect" the lines:
        # todo: review since hard-coded!
        if self.verbose:
            print '.. connecting to server MongoClient ("127.0.0.1", 27017)'
        self.pongo = MongoClient("127.0.0.1", 27017)
 and update them accordingly with the port the mongo server diaplyed in the preceding step (in our case "27017")
- by default the code displays the result on a web-page (localhost). But you may also wish to display as MatplotLib Client instead. This is actually customizable in the <i>Graph->prepare_graph(self)</i> with the activation of 1 of these options:
    - mpld3.show()
    - plt.show()
- <b>now run</b> the Python file <i>openfoodfacts.py</i>. If the number of products is not 0, it then means that the connection to the server was successful, and you may go further
- When asked to enter a product code, you may either press RETURN (in which case a default product is chosen), or enter a product code which is available in the OFF-database locally:
<br/><br/>
    verbose = True
<br/>
    .. connecting to server MongoClient ("127.0.0.1", 27017)
<br/>
    .. connecting to OPENFOODFACTS database
<br/>
    .. getting PRODUCTS collection
<br/>
    68483 products are referenced
<br/>
<br/>
    please enter a product code ['q'uit] &gt; 
<br/>
- similar products are then fetched and scores are computed, which may take some time.
- When you finally see the following messages (this may take some minutes!), then your graph is ready and displaayed hopefully:
    - 127.0.0.1 - - [15/Apr/2016 19:38:33] "GET / HTTP/1.1" 200 -
    - 127.0.0.1 - - [15/Apr/2016 19:38:33] "GET /d3.js HTTP/1.1" 200 -
    -   127.0.0.1 - - [15/Apr/2016 19:38:33] "GET /mpld3.js HTTP/1.1" 200 -
    - 127.0.0.1 - - [15/Apr/2016 19:38:34] code 404, message Not Found
    - 127.0.0.1 - - [15/Apr/2016 19:38:34] "GET /favicon.ico HTTP/1.1" 404 -
- the black point along with the white square refers to the reference product (similarity of 100% and its nutrition score). All other points are the fetched more-or-less similar products. Within a square, these products are displayed according to a specific algorithm for the repartition of points in a disk-surface (this has been my own decision and is arbitrary)
- Plot your mouse on any point to see some details of the matching product

<h1>Current bugs</h1>
- Matplotlib Client graph displays the back point for the reference product correctly, but the corresponding white square is mirrored (probably a discrepancy between plot in mpld3 and matplotlib)
- whereas plot shows correct axis data, mpld3 doesn't (bug referenced in http://stackoverflow.com/questions/35446525/setting-tick-labels-in-mpld3)

<h1>Things to be done next</h1>
- performance has to be improved in many ways:
    - the lower the similarity, the less points we need to retrieve (boundary instead of all products)
    - adding filtering criteria (country, ...)
- dispaly on a web page with labels, urls, and images in ajax-mode (see <i>http://world.openfoodfacts.org/cgi/search.pl?action=process&tagtype_0=categories&tag_contains_0=contains&tag_0=Breakfast%20cereals&sort_by=unique_scans_n&page_size=20&axis_x=sugars&axis_y=fat&series_nutrition_grades=on&graph=1</i>). We may take the same libraries instead of <i>mpld3</i>
- nutrition scores are France-based and may be different in other countries
- nutrition scores should differentiate between waters and beverages (see <i>http://fr.openfoodfacts.org/score-nutritionnel-france</i>)
- in the web-page, possible addition of fields (country, ...) to display only products of customer's country and also to reduce the number of matching products (performance)
