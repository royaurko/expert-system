# Ask Minmax!

Ask Minmax is an expert system for optimization problems targeted towards the non-expert user.


## How it works
 * Ask-minmax associates a **prior** to every problem and question in the database. 
 * The prior of a problem is proportional to the number of times there is a query intended for that particular
  problem. 
 * The prior of a question reflects the **gain in information** by asking the question  - in other words
 it is inversely proportional to the **expected conditional entropy** of the distribution of problem posteriors
 conditioned on the response to this question.
 * At every step a question is sampled proportional to it's posterior.
 * The posteriors of a problem are updated according to the **confidence** level in your answer.
 * The posteriors of a question are updated reflecting the information gain provided for this new distribution.
 * The algorithm outputs the most popular problems by doing a 1 dimensional k-means (a.k.a
[Jenks natural breaks](https://en.wikipedia.org/wiki/Jenks_natural_breaks_optimization) ).
 * A similar (clustering) idea is applied to questions, at every step only the "most useful questions" are
  sampled from.
 * The algorithm is greedy in the sense that it only cares about questions that reduce the entropy on the
 posterior distribution supported on the "most relevant" (coming from Jenks/k-means) problems.
 * You can visualizes the changing distribution in a simple matplotlib plot.
 
## Other stuff
 
 * You can store the database files as a BSON object (stored in `database/db`).
 * To see the code organization see [organization.md](src/askminmax/organization.md)
 * Comes with a small default [database](database/db)
 
## Prerequisites: 
 * Python 2.7
 * A running [Mongodb](https://www.mongodb.org/) server 
 * [pymongo](https://pypi.python.org/pypi/pymongo/)
 * [jenks](https://github.com/perrygeo/jenks)
 * [scipy](http://www.scipy.org/)
 * [numpy](http://www.scipy.org/)
 * [matplotlib](http://matplotlib.org/)
 
 The following dependencies are due to Google's word2vec model (this part is work in progress):
 * [nltk](http://www.nltk.org/)
 * [scikit-learn](https://pypi.python.org/pypi/scikit-learn/0.16.1)
 * [gensim](https://pypi.python.org/pypi/gensim)

## Quick Start:

Clone the repository and install it as a library using 

```shell
sudo python setup.py install
```

To create an instance of the Expert system first import the `Expert` class and
then use the basic constructor

```python
from askminmax.expert import Expert
expert = Expert()
```

It will ask you to either import stuff from an existing database or it will give 
you the option to create one of your own. Finally to run the expert system use

```python
expert.run()
```