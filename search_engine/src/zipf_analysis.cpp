#include "zipf_analysis.h"
#include <fstream>
#include <iostream>

ZipfAnalyzer::ZipfAnalyzer() {}

void ZipfAnalyzer::add_term(const std::string& term) {
    int freq;
    if (term_frequencies_.find(term, freq)) {
        term_frequencies_.insert(term, freq + 1);
    } else {
        term_frequencies_.insert(term, 1);
    }
}

void ZipfAnalyzer::sort_by_frequency() {
    sorted_terms_.clear();
    
    for (auto it = term_frequencies_.begin(); it != term_frequencies_.end(); ++it) {
        sorted_terms_.push_back(TermFrequency(it.key(), it.value()));
    }
    
    for (size_t i = 0; i < sorted_terms_.size(); ++i) {
        for (size_t j = i + 1; j < sorted_terms_.size(); ++j) {
            if (sorted_terms_[j].frequency > sorted_terms_[i].frequency) {
                TermFrequency temp = sorted_terms_[i];
                sorted_terms_[i] = sorted_terms_[j];
                sorted_terms_[j] = temp;
            }
        }
    }
    
    for (size_t i = 0; i < sorted_terms_.size(); ++i) {
        sorted_terms_[i].rank = i + 1;
    }
}

void ZipfAnalyzer::finalize() {
    sort_by_frequency();
}

void ZipfAnalyzer::save_to_csv(const std::string& filename) const {
    std::ofstream file(filename);
    if (!file.is_open()) {
        std::cerr << "Failed to open " << filename << " for writing\n";
        return;
    }
    
    file << "rank,frequency,term\n";
    
    size_t limit = sorted_terms_.size() < 10000 ? sorted_terms_.size() : 10000;
    for (size_t i = 0; i < limit; ++i) {
        file << sorted_terms_[i].rank << ","
             << sorted_terms_[i].frequency << ","
             << sorted_terms_[i].term << "\n";
    }
    
    file.close();
    std::cout << "Zipf analysis saved to " << filename << "\n";
    std::cout << "Vocabulary size: " << sorted_terms_.size() << "\n";
    if (sorted_terms_.size() > 0) {
        std::cout << "Most frequent term: " << sorted_terms_[0].term 
                  << " (frequency: " << sorted_terms_[0].frequency << ")\n";
    }
}

size_t ZipfAnalyzer::vocabulary_size() const {
    return sorted_terms_.size();
}

size_t ZipfAnalyzer::total_terms() const {
    size_t total = 0;
    for (size_t i = 0; i < sorted_terms_.size(); ++i) {
        total += sorted_terms_[i].frequency;
    }
    return total;
}
