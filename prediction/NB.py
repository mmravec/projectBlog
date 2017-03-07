from collections import Counter
import glob, os
import re
import numpy as np

x = []

def remove_stopwords(words):
    print('Loading all stop words...')
    stopwords = ['all', 'just', 'being', 'over', 'both', 'through', 'yourselves', 'its', 'before', 'herself', 'had',
                 'should', 'to', 'only', 'under', 'ours', 'has', 'do', 'them', 'his', 'very', 'they', 'not', 'during',
                 'now', 'him', 'nor', 'did', 'this', 'she', 'each', 'further', 'where', 'few', 'because', 'doing',
                 'some', 'are', 'our', 'ourselves', 'out', 'what', 'for', 'while', 'does', 'above', 'between', 't',
                 'be', 'we', 'who', 'were', 'here', 'hers', 'by', 'on', 'about', 'of', 'against', 's', 'or', 'own',
                 'into', 'yourself', 'down', 'your', 'from', 'her', 'their', 'there', 'been', 'whom', 'too',
                 'themselves', 'was', 'until', 'more', 'himself', 'that', 'but', 'don', 'with', 'than', 'those', 'he',
                 'me', 'myself', 'these', 'up', 'will', 'below', 'can', 'theirs', 'my', 'and', 'then', 'is', 'am', 'it',
                 'an', 'as', 'itself', 'at', 'have', 'in', 'any', 'if', 'again', 'no', 'when', 'same', 'how', 'other',
                 'which', 'you', 'after', 'most', 'such', 'why', 'a', 'off', 'i', 'yours', 'so', 'the', 'having',
                 'once']
    print('Loading stopwords success 100%!')
    str1 = ''.join(words)
    my_string = str1.lower().split()
    print('Loading text success 100%')
    my_dict = {}
    for word in my_string:
        if len(word) > 2 and re.match("^[a-zA-Z0-9_]*$", word):
            if word.lower() not in stopwords:
                if word.lower() in my_dict:
                    my_dict[word.lower()] += 1
                else:
                    my_dict[word.lower()] = 1
    print(my_dict)
    print('Remove stopwords dome!')
    return my_dict

os.chdir("/Users/martinmravec/Documents/mix20_rand700_tokens_0211/tokens/pos")
for file in glob.glob("*.txt"):
    p = open(file, 'r', encoding='ISO-8859-1')
    reviewsP = list(p)
    reviewsP.append('1')
    x.append(reviewsP)
    #print(reviewsP)
    # print(file)

os.chdir("/Users/martinmravec/Documents/mix20_rand700_tokens_0211/tokens/neg")
for file in glob.glob("*.txt"):
    n = open(file, 'r', encoding='ISO-8859-1')
    reviewsN = list(n)
    reviewsN.append('-1')
    x.append(reviewsN)
    #print(reviewsP)
    # print(file)

def get_text(x, score):
  # Join together the text in the reviews for a particular tone.
  return " ".join([r[0].lower() for r in x if r[1] == str(score)])


# def count_text(text):
#   # Split text into words based on whitespace.  Simple but effective.
#   words = re.split("\s+", text)
#   # Count up the occurence of each word.
#   return Counter(words)

negative_text = get_text(x, -1)
positive_text = get_text(x, 1)

negative_counts = remove_stopwords(negative_text)

positive_counts = remove_stopwords(positive_text)

# print("Negative text sample: {0}".format(negative_text[:50]))
# print("Positive text sample: {0}".format(positive_text[:50]))


def get_y_count(score):
  # Compute the count of each classification occuring in the data.
  return len([r for r in x if r[1] == str(score)])

positive_review_count = get_y_count(1)
negative_review_count = get_y_count(-1)

# These are the class probabilities (we saw them in the formula as P(y)).
prob_positive = positive_review_count / len(x)
prob_negative = negative_review_count / len(x)

def make_class_prediction(text, counts, class_prob, class_count):
  prediction = 1
  # text = remove_stopwords(text)
  #text_counts = Counter(re.split("\s+", text))
  text_counts = remove_stopwords(text)
  for word in text_counts:
          # For every word in the text, we get the number of times that word occured in the reviews for a given class, add 1 to smooth the value, and divide by the total number of words in the class (plus the class_count to also smooth the denominator).
          prediction *= np.longfloat(text_counts.get(word) * ((counts.get(word, 0) + 1) / (sum(counts.values()) + class_count)))
  # Now we multiply by the probability of the class existing in the documents.
  return prediction * class_prob
