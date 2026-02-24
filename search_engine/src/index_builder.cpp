#include "index_builder.h"
#include <iostream>
#include <fstream>
#include <sstream>

IndexBuilder::IndexBuilder() {}

void IndexBuilder::add_document(int doc_id, const std::string& url, 
                                const std::string& title, const std::string& text) {
    while (doc_urls_.size() <= static_cast<size_t>(doc_id)) {
        doc_urls_.push_back("");
        doc_titles_.push_back("");
        doc_lengths_.push_back(0);
    }
    
    doc_urls_[doc_id] = url;
    doc_titles_[doc_id] = title;

    stats_.total_text_bytes += static_cast<long long>(text.length());
    
    DynamicArray<std::string> tokens = tokenizer_.tokenize(text);
    
    doc_lengths_[doc_id] = tokens.size();
    stats_.total_tokens += static_cast<long long>(tokens.size());

    for (size_t i = 0; i < tokens.size(); ++i) {
        stats_.total_token_chars += static_cast<long long>(tokens[i].length());
    }
    
    HashMap<std::string, int> term_freqs;
    for (size_t i = 0; i < tokens.size(); ++i) {
        std::string stem = stemmer_.stem(tokens[i]);
        if (stem.empty()) {
            continue;
        }

        stats_.total_stems++;
        stats_.total_stem_chars += static_cast<long long>(stem.length());

        zipf_.add_term(stem);

        int current_tf = 0;
        if (term_freqs.find(stem, current_tf)) {
            term_freqs.insert(stem, current_tf + 1);
        } else {
            term_freqs.insert(stem, 1);
        }
    }

    for (auto it = term_freqs.begin(); it != term_freqs.end(); ++it) {
        std::string stem = it.key();
        int tf = it.value();

        DynamicArray<TermPosting> posting_list;
        if (inverted_index_.find(stem, posting_list)) {
            posting_list.push_back(TermPosting(doc_id, tf));
            inverted_index_.insert(stem, posting_list);
        } else {
            posting_list.push_back(TermPosting(doc_id, tf));
            inverted_index_.insert(stem, posting_list);
        }
    }
}

std::string IndexBuilder::extract_json_field(const std::string& json, const std::string& field_name, size_t start_pos) {
    size_t field_pos = json.find("\"" + field_name + "\":", start_pos);
    if (field_pos == std::string::npos) return "";
    
    size_t value_start = json.find(":", field_pos) + 1;
    while (value_start < json.length() && (json[value_start] == ' ' || json[value_start] == '\t')) {
        value_start++;
    }
    
    if (json[value_start] != '"') {
        size_t value_end = json.find(",", value_start);
        if (value_end == std::string::npos) value_end = json.find("}", value_start);
        return json.substr(value_start, value_end - value_start);
    }
    
    value_start++;
    std::string result;
    for (size_t i = value_start; i < json.length(); ++i) {
        if (json[i] == '\\' && i + 1 < json.length()) {
            i++;
            if (json[i] == 'n') result += '\n';
            else if (json[i] == 't') result += '\t';
            else if (json[i] == 'r') result += '\r';
            else result += json[i];
        } else if (json[i] == '"') {
            break;
        } else {
            result += json[i];
        }
    }
    
    return result;
}

void IndexBuilder::build_from_jsonl(const std::string& input_file) {
    std::ifstream file(input_file);
    if (!file.is_open()) {
        std::cerr << "Failed to open " << input_file << "\n";
        return;
    }
    
    std::cout << "Building index from " << input_file << "...\n";
    
    std::string line;
    int doc_count = 0;
    
    while (std::getline(file, line)) {
        if (line.empty() || line.length() < 50) continue;
        
        std::string doc_id_str = extract_json_field(line, "doc_id", 0);
        if (doc_id_str.empty()) continue;
        
        int doc_id = std::stoi(doc_id_str);
        std::string url = extract_json_field(line, "url", 0);
        std::string title = extract_json_field(line, "title", 0);
        std::string text = extract_json_field(line, "text", 0);
        
        if (text.empty() || text.length() < 50) continue;
        
        add_document(doc_id, url, title, text);
        
        doc_count++;
        if (doc_count % 1000 == 0) {
            std::cout << "Processed " << doc_count << " documents...\n";
        }
    }
    
    file.close();
    stats_.doc_count = doc_count;
    
    std::cout << "Index building complete!\n";
    std::cout << "Total documents: " << doc_count << "\n";
    std::cout << "Vocabulary size: " << inverted_index_.size() << "\n";
}

long long IndexBuilder::total_postings() {
    long long total = 0;
    for (auto it = inverted_index_.begin(); it != inverted_index_.end(); ++it) {
        total += static_cast<long long>(it.value().size());
    }
    return total;
}

void IndexBuilder::save_index(const std::string& index_dir) {
    std::ofstream vocab_file(index_dir + "/vocabulary.txt");
    std::ofstream index_file(index_dir + "/index.bin", std::ios::binary);
    std::ofstream doc_file(index_dir + "/documents.txt");
    std::ofstream lengths_file(index_dir + "/doc_lengths.txt");
    
    if (!vocab_file.is_open() || !index_file.is_open() || 
        !doc_file.is_open() || !lengths_file.is_open()) {
        std::cerr << "Failed to open index files for writing\n";
        return;
    }
    
    int term_id = 0;
    for (auto it = inverted_index_.begin(); it != inverted_index_.end(); ++it) {
        std::string term = it.key();
        DynamicArray<TermPosting> posting_list = it.value();
        
        vocab_file << term_id << " " << term << " " << posting_list.size() << "\n";
        
        int list_size = posting_list.size();
        index_file.write(reinterpret_cast<const char*>(&list_size), sizeof(int));
        for (size_t i = 0; i < posting_list.size(); ++i) {
            index_file.write(reinterpret_cast<const char*>(&posting_list[i].doc_id), sizeof(int));
            index_file.write(reinterpret_cast<const char*>(&posting_list[i].tf), sizeof(int));
        }
        
        term_id++;
    }
    
    for (size_t i = 0; i < doc_urls_.size(); ++i) {
        doc_file << i << "\t" << doc_urls_[i] << "\t" << doc_titles_[i] << "\n";
    }
    
    for (size_t i = 0; i < doc_lengths_.size(); ++i) {
        lengths_file << doc_lengths_[i] << "\n";
    }
    
    vocab_file.close();
    index_file.close();
    doc_file.close();
    lengths_file.close();
    
    std::cout << "Index saved to " << index_dir << "/\n";
}

void IndexBuilder::save_zipf_analysis(const std::string& filename) {
    zipf_.finalize();
    zipf_.save_to_csv(filename);
}
