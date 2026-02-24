#include "tokenizer.h"

Tokenizer::Tokenizer() {
    init_stop_words();
}

void Tokenizer::init_stop_words() {
    const char* stop_words_array[] = {
        "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
        "has", "he", "in", "is", "it", "its", "of", "on", "that", "the",
        "to", "was", "were", "will", "with", "this", "but", "they", "have",
        "had", "what", "when", "where", "who", "which", "why", "how", "all",
        "each", "every", "both", "few", "more", "most", "other", "some", "such",
        "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very",
        "can", "just", "should", "now",
        "you", "your", "we", "our", "us", "or", "if", "do", "did", "does",
        "about", "up", "out", "would", "could", "may", "might", "been",
        "also", "into", "over", "after", "before", "through", "between",
        "her", "him", "his", "she", "them", "their", "my", "me",
        "any", "there", "then", "these", "those", "am", "been", "being",
        "here", "while", "during", "under", "again", "once"
    };
    
    size_t count = sizeof(stop_words_array) / sizeof(stop_words_array[0]);
    for (size_t i = 0; i < count; ++i) {
        stop_words_.push_back(std::string(stop_words_array[i]));
    }
}

bool Tokenizer::is_stop_word(const std::string& word) const {
    for (size_t i = 0; i < stop_words_.size(); ++i) {
        if (stop_words_[i] == word) {
            return true;
        }
    }
    return false;
}

std::string Tokenizer::to_lower(const std::string& str) const {
    std::string result;
    result.reserve(str.length());
    for (char c : str) {
        result += std::tolower(static_cast<unsigned char>(c));
    }
    return result;
}

bool Tokenizer::is_alpha(char c) const {
    return std::isalpha(static_cast<unsigned char>(c));
}

DynamicArray<std::string> Tokenizer::tokenize(const std::string& text) const {
    DynamicArray<std::string> tokens;
    std::string current_token;
    
    for (size_t i = 0; i < text.length(); ++i) {
        char c = text[i];
        
        if (is_alpha(c) || (c == '\'' && !current_token.empty())) {
            current_token += c;
        } else {
            if (!current_token.empty()) {
                std::string lower_token = to_lower(current_token);
                
                if (lower_token.length() >= 2 && !is_stop_word(lower_token)) {
                    tokens.push_back(lower_token);
                }
                current_token.clear();
            }
        }
    }
    
    if (!current_token.empty()) {
        std::string lower_token = to_lower(current_token);
        if (lower_token.length() >= 2 && !is_stop_word(lower_token)) {
            tokens.push_back(lower_token);
        }
    }
    
    return tokens;
}
