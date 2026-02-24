#include "index_builder.h"
#include <iostream>
#include <chrono>
#include <iomanip>

int main(int argc, char* argv[]) {
    std::string input_file = "../../documents.jsonl";
    std::string index_dir = "../index";
    std::string zipf_file = "../zipf_stats.csv";
    
    if (argc > 1) {
        input_file = argv[1];
    }
    if (argc > 2) {
        index_dir = argv[2];
    }
    if (argc > 3) {
        zipf_file = argv[3];
    }
    
    std::cout << "=== Boolean Search Engine - Index Builder ===\n";
    std::cout << "Input file: " << input_file << "\n";
    std::cout << "Index directory: " << index_dir << "\n";
    std::cout << "Zipf analysis file: " << zipf_file << "\n\n";
    
    IndexBuilder builder;

    auto t0 = std::chrono::high_resolution_clock::now();
    builder.build_from_jsonl(input_file);
    auto t1 = std::chrono::high_resolution_clock::now();

    builder.save_index(index_dir);
    builder.save_zipf_analysis(zipf_file);

    double elapsed = std::chrono::duration<double>(t1 - t0).count();
    const auto& s = builder.stats();
    long long postings = builder.total_postings();
    size_t vocab = builder.vocabulary_size();

    std::cout << std::fixed;
    std::cout << "\n=== Statistics ===\n";
    std::cout << "documents=" << s.doc_count << "\n";
    std::cout << "total_tokens=" << s.total_tokens << "\n";
    std::cout << "total_stems=" << s.total_stems << "\n";
    std::cout << "avg_tokens_per_doc=" << std::setprecision(1)
              << (s.doc_count > 0 ? (double)s.total_tokens / s.doc_count : 0) << "\n";
    std::cout << "avg_token_length=" << std::setprecision(2)
              << (s.total_tokens > 0 ? (double)s.total_token_chars / s.total_tokens : 0) << "\n";
    std::cout << "avg_stem_length=" << std::setprecision(2)
              << (s.total_stems > 0 ? (double)s.total_stem_chars / s.total_stems : 0) << "\n";
    double tok_len = s.total_tokens > 0 ? (double)s.total_token_chars / s.total_tokens : 0;
    double stem_len = s.total_stems > 0 ? (double)s.total_stem_chars / s.total_stems : 0;
    double reduction = tok_len > 0 ? 100.0 * (tok_len - stem_len) / tok_len : 0;
    std::cout << "stem_length_reduction=" << std::setprecision(1) << reduction << "%\n";
    std::cout << "vocabulary_size=" << vocab << "\n";
    std::cout << "total_postings=" << postings << "\n";
    std::cout << "avg_postings_per_term=" << std::setprecision(1)
              << (vocab > 0 ? (double)postings / vocab : 0) << "\n";
    std::cout << "text_bytes_total=" << s.total_text_bytes << "\n";
    std::cout << "elapsed_seconds=" << std::setprecision(2) << elapsed << "\n";
    double kb = (double)s.total_text_bytes / 1024.0;
    std::cout << "seconds_per_kb=" << std::setprecision(6)
              << (kb > 0 ? elapsed / kb : 0) << "\n";
    
    std::cout << "\n=== Index building complete! ===\n";
    
    return 0;
}
