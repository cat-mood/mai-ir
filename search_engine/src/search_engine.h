#ifndef SEARCH_ENGINE_H
#define SEARCH_ENGINE_H

#include <string>
#include "data_structures.h"
#include "tokenizer.h"
#include "stemmer.h"

struct SearchPosting {
    int doc_id;
    int tf;

    SearchPosting() : doc_id(-1), tf(0) {}
    SearchPosting(int id, int term_freq) : doc_id(id), tf(term_freq) {}
};

struct SearchResult {
    int doc_id;
    std::string url;
    std::string title;
    
    SearchResult() : doc_id(-1) {}
    SearchResult(int id, const std::string& u, const std::string& t) 
        : doc_id(id), url(u), title(t) {}
};

class SearchEngine {
private:
    HashMap<std::string, DynamicArray<SearchPosting>> inverted_index_;
    DynamicArray<std::string> doc_urls_;
    DynamicArray<std::string> doc_titles_;
    DynamicArray<int> doc_lengths_;
    Tokenizer tokenizer_;
    PorterStemmer stemmer_;
    
    DynamicArray<int> intersect(const DynamicArray<int>& list1, const DynamicArray<int>& list2);
    DynamicArray<int> union_lists(const DynamicArray<int>& list1, const DynamicArray<int>& list2);
    DynamicArray<int> difference(const DynamicArray<int>& list1, const DynamicArray<int>& list2);
    DynamicArray<int> all_document_ids() const;
    DynamicArray<int> posting_doc_ids(const std::string& stemmed_term) const;
    DynamicArray<std::string> to_rpn(const DynamicArray<std::string>& tokens) const;
    DynamicArray<int> eval_rpn(const DynamicArray<std::string>& rpn_tokens);
    bool contains_doc(const DynamicArray<SearchPosting>& posting_list, int doc_id) const;
    int term_tf_for_doc(const DynamicArray<SearchPosting>& posting_list, int doc_id) const;
    bool is_operator_token(const std::string& token) const;
    int operator_precedence(const std::string& op) const;
    bool is_left_associative(const std::string& op) const;
    std::string normalize_query_token(const std::string& token) const;
    std::string to_lower_ascii(const std::string& text) const;
    DynamicArray<std::string> extract_query_terms(const DynamicArray<std::string>& tokens);
    double compute_doc_score(int doc_id, const DynamicArray<std::string>& query_terms) const;
    
public:
    SearchEngine();
    bool load_index(const std::string& index_dir);
    DynamicArray<SearchResult> search(const std::string& query, size_t* total_matches = nullptr);
};

#endif
