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
- now run the Python file <i>openfoodfacts.py</i>. If the number of products is not 0, it then means that the connection to the server was successful, and you may go further
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


<h1>Current bugs</h1>

<h1>Things to be done next</h1>
- url
- image of product (Ajax)
