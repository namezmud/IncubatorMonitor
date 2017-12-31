import bokeh
import sklearn
import numpy as np
import json
from sklearn import svm
from sklearn import preprocessing

# Implement a classifier using an SVM for classifying egg/not_an_egg from images.
class ML():

##with open('res.json') as json_data:
##     d = json.load(json_data)
##     print(d)

    def _extract_features(self, x):
        features = [x["error"], x["ellipse"][1][0], x["ellipse"][1][1], x["ellipse"][1][1]/x["ellipse"][1][0]] + x["median_ints"]
        return features

    # With a trained SVM predict which are eggs.
    def predict(self, raw):

        X = [self._extract_features(x) for x in raw]
        scaled = self.scaler.transform(X)
        pred = self.clf.predict(scaled)
        return pred

    # Run test data through the trained SVM and get statistics.
    def run_test(self):
        X_test = self.scaler.transform(self.X_test)
        self.pred = self.clf.predict(X_test)

        self.True_test = [i for i in range(len(self.Y_test))
                          if self.Y_test[i] > 0]
        self.False_test = [i for i in range(len(self.Y_test))
                           if self.Y_test[i] == 0]

        print("True positive ", np.mean(self.pred[self.True_test]))
        print("False positive ", np.mean(self.pred[self.False_test]))

    # set the data to train the SVM and perform the training.
    def setData(self, raw):
        # extract 80% as training and 20% as test data
        self.train = [raw[i] for i in range(len(raw)) if i%5]
        self.test = [raw[i] for i in range(len(raw)) if i%5==0]
        print("Train/Test data ", len(self.train), len(self.test))

        #extract feature vectors from the dictionary of classified data
        self.X_train = [[x["error"], x["ellipse"][1][0], x["ellipse"][1][1],
                         x["ellipse"][1][1]/x["ellipse"][1][0]] + x["median_ints"] for x in self.train]
        if not np.isfinite(self.X_train).all():
            print(" Bad X_train ")

        #extract classifications
        Y = [x['classification'] == 'EGG' for x in self.train]
        self.Y_train = np.array(Y).astype(int)

        self.X_test = [[x["error"], x["ellipse"][1][0], x["ellipse"][1][1],
                        x["ellipse"][1][1]/x["ellipse"][1][0]] + x["median_ints"] for x in self.test]
        Y = [x['classification'] == 'EGG' for x in self.test]
        self.Y_test = np.array(Y).astype(int)

        # scale the data with zero mean and std deviation.
        self.scaler = preprocessing.StandardScaler().fit(self.X_train)
        X_scaled = self.scaler.transform(self.X_train)

        #train an svm
        self.clf = svm.SVC()
        self.clf.fit(X_scaled, self.Y_train)
