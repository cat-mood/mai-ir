#include "stemmer.h"
#include <gtest/gtest.h>

TEST(PorterStemmer, StemRunning) {
    PorterStemmer stemmer;
    EXPECT_EQ(stemmer.stem("running"), "run");
}

TEST(PorterStemmer, StemPonies) {
    PorterStemmer stemmer;
    EXPECT_EQ(stemmer.stem("ponies"), "poni");
}

TEST(PorterStemmer, StemNational) {
    PorterStemmer stemmer;
    EXPECT_EQ(stemmer.stem("national"), "nation");
}

TEST(PorterStemmer, StemGeneralization) {
    PorterStemmer stemmer;
    EXPECT_EQ(stemmer.stem("generalization"), "gener");
}

TEST(PorterStemmer, StemEffective) {
    PorterStemmer stemmer;
    EXPECT_EQ(stemmer.stem("effective"), "effect");
}
