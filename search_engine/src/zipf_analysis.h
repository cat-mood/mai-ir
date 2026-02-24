#ifndef ZIPF_ANALYSIS_H
#define ZIPF_ANALYSIS_H

#include <string>
#include "data_structures.h"

struct TermFrequency {
    std::string term;
    int frequency;
    int rank;
    
    TermFrequency() : frequency(0), rank(0) {}
    TermFrequency(const std::string& t, int f) : term(t), frequency(f), rank(0) {}
};

class ZipfAnalyzer {
private:
    HashMap<std::string, int> term_frequencies_;
    DynamicArray<TermFrequency> sorted_terms_;
    
    void sort_by_frequency();
    
public:
    ZipfAnalyzer();
    void add_term(const std::string& term);
    void finalize();
    void save_to_csv(const std::string& filename) const;
    size_t vocabulary_size() const;
    size_t total_terms() const;
};

#endif
