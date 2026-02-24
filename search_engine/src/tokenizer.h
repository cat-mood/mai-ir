#ifndef TOKENIZER_H
#define TOKENIZER_H

#include <string>
#include <cctype>
#include "data_structures.h"

class Tokenizer {
private:
    DynamicArray<std::string> stop_words_;
    
    void init_stop_words();
    bool is_stop_word(const std::string& word) const;
    std::string to_lower(const std::string& str) const;
    bool is_alpha(char c) const;
    
public:
    Tokenizer();
    DynamicArray<std::string> tokenize(const std::string& text) const;
};

#endif
