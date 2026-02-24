#include "tokenizer.h"
#include <gtest/gtest.h>

TEST(Tokenizer, ReturnsNonEmpty) {
    Tokenizer tokenizer;
    std::string text = "The quick brown fox jumps over the lazy dog";
    DynamicArray<std::string> tokens = tokenizer.tokenize(text);

    EXPECT_GT(tokens.size(), 0);
}

TEST(Tokenizer, RemovesStopWords) {
    Tokenizer tokenizer;
    std::string text = "The quick brown fox jumps over the lazy dog";
    DynamicArray<std::string> tokens = tokenizer.tokenize(text);

    bool has_the = false;
    for (size_t i = 0; i < tokens.size(); ++i) {
        if (tokens[i] == "the") {
            has_the = true;
            break;
        }
    }
    EXPECT_FALSE(has_the);
}

TEST(Tokenizer, KeepsContentWords) {
    Tokenizer tokenizer;
    std::string text = "The quick brown fox jumps over the lazy dog";
    DynamicArray<std::string> tokens = tokenizer.tokenize(text);

    bool has_quick = false;
    for (size_t i = 0; i < tokens.size(); ++i) {
        if (tokens[i] == "quick") {
            has_quick = true;
            break;
        }
    }
    EXPECT_TRUE(has_quick);
}
