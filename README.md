<h1>Purpose</h1>
This application is in a draft version and is bound to the openfoodfacts.org application.
It runs currently in a console mode, but displays its results as a graph on localhost (web display).
After having entered a product reference (in the same way as in <it>www.openfoodfacts.org</it>), it will seek for similar products in the OFF database and display them on a graph based on their nutrition-score (grades A to E) and their similarity with the product reference.
It makes it then possible to the consumer to look for more or less similar products with better nutrition properties if wanted.

<h1>Requirements</h1>
Proceed first with the setup described here: http://openfoodfacts.github.io/OpenFoodFacts-APIRestPython/

<h1>How it works?</h1>
Once you have entered a product reference in the command line, the application fetches a subset of information for this product, and especially the <it>nutriments</it> (for computing the nutrition score) and the <it>categories_tags</it> (for fetching more or less similar products).
The application then fetches in the database all products for each entry of the <it>categories_tags</it> which the reference product belongs to (this is surely not optimal!). The intersection of the categories_tags for fetched products and the reference product is computed. The higher the intersection, the closer the similarity with the reference product; so for now, the "score proximity" of a product with the reference product is computed as follows:
<nb of intersected categories_tags of product X> / <nb of categories_tags of reference product>
Note: if all categories_tags of the reference product are listed in another product, then the match is 1, i.e. 100%

<h1>How to start</h1>
Once the OFF database is decompacted (see "Requirements" above), perform the following actions:


<h1>Current bugs</h1>

<h1>Things to be done next</h1>
- url
- image of product (Ajax)
