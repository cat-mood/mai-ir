#ifndef INDEX_BUILDER_H
#define INDEX_BUILDER_H

#include <string>
#include <fstream>
#include "data_structures.h"
#include "tokenizer.h"
#include "stemmer.h"
#include "zipf_analysis.h"

struct TermPosting {
    int doc_id;
    int tf;

    TermPosting() : doc_id(-1), tf(0) {}
    TermPosting(int id, int term_freq) : doc_id(id), tf(term_freq) {}
};

struct BuildStats {
    long long total_tokens = 0;
    long long total_stems = 0;
    long long total_token_chars = 0;
    long long total_stem_chars = 0;
    long long total_text_bytes = 0;
    int doc_count = 0;
};

class IndexBuilder {
private:
    HashMap<std::string, DynamicArray<TermPosting>> inverted_index_;
    DynamicArray<std::string> doc_urls_;
    DynamicArray<std::string> doc_titles_;
    DynamicArray<int> doc_lengths_;
    Tokenizer tokenizer_;
    PorterStemmer stemmer_;
    ZipfAnalyzer zipf_;
    BuildStats stats_;
    
    std::string extract_json_field(const std::string& json, const std::string& field_name, size_t start_pos);
    
public:
    IndexBuilder();
    void add_document(int doc_id, const std::string& url, const std::string& title, const std::string& text);
    void build_from_jsonl(const std::string& input_file);
    void save_index(const std::string& index_dir);
    void save_zipf_analysis(const std::string& filename);
    const BuildStats& stats() const { return stats_; }
    size_t vocabulary_size() const { return inverted_index_.size(); }
    long long total_postings();
};

#endif
