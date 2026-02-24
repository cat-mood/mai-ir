#include "search_engine.h"
#include <iostream>
#include <string>
#include <chrono>
#include <iomanip>

int main(int argc, char* argv[]) {
    std::string index_dir = "../index";
    
    if (argc > 1) {
        index_dir = argv[1];
    }
    
    SearchEngine engine;
    
    if (!engine.load_index(index_dir)) {
        std::cerr << "Failed to load index from " << index_dir << "\n";
        return 1;
    }
    
    std::cout << "\n=== Boolean Search Engine - CLI ===\n";
    std::cout << "Enter queries (one per line). Operators: AND, OR, NOT\n";
    std::cout << "Example: fallout AND vault OR pip-boy NOT nuka-cola\n";
    std::cout << "Press Ctrl+D (Unix) or Ctrl+Z (Windows) to exit.\n\n";
    
    std::string query;
    while (std::getline(std::cin, query)) {
        if (query.empty()) {
            continue;
        }

        size_t total = 0;
        auto t0 = std::chrono::high_resolution_clock::now();
        DynamicArray<SearchResult> results = engine.search(query, &total);
        auto t1 = std::chrono::high_resolution_clock::now();
        double ms = std::chrono::duration<double, std::milli>(t1 - t0).count();

        std::cout << "Found " << total << " documents"
                  << std::fixed << std::setprecision(1)
                  << " (" << ms << " ms):\n";
        
        size_t display_limit = results.size() < 100 ? results.size() : 100;
        for (size_t i = 0; i < display_limit; ++i) {
            std::cout << results[i].doc_id << "\t" 
                     << results[i].url << "\t" 
                     << results[i].title << "\n";
        }
        
        if (results.size() > display_limit) {
            std::cout << "... and " << (results.size() - display_limit) << " more results\n";
        }
        
        std::cout << "\n";
    }
    
    return 0;
}
