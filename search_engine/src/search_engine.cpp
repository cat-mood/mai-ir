#include "search_engine.h"
#include <iostream>
#include <fstream>
#include <sstream>
#include <cctype>
#include <cmath>

SearchEngine::SearchEngine() {}

bool SearchEngine::load_index(const std::string& index_dir) {
    std::ifstream vocab_file(index_dir + "/vocabulary.txt");
    std::ifstream index_file(index_dir + "/index.bin", std::ios::binary);
    std::ifstream doc_file(index_dir + "/documents.txt");
    std::ifstream lengths_file(index_dir + "/doc_lengths.txt");
    
    if (!vocab_file.is_open() || !index_file.is_open() || !doc_file.is_open()) {
        std::cerr << "Failed to open index files\n";
        return false;
    }
    
    std::cout << "Loading index from " << index_dir << "...\n";
    
    std::string line;
    while (std::getline(vocab_file, line)) {
        std::istringstream iss(line);
        int term_id;
        std::string term;
        int doc_freq;
        
        iss >> term_id >> term >> doc_freq;
        
        DynamicArray<SearchPosting> posting_list;
        int actual_size;
        index_file.read(reinterpret_cast<char*>(&actual_size), sizeof(int));
        
        for (int i = 0; i < actual_size; ++i) {
            int doc_id;
            int tf;
            index_file.read(reinterpret_cast<char*>(&doc_id), sizeof(int));
            index_file.read(reinterpret_cast<char*>(&tf), sizeof(int));
            posting_list.push_back(SearchPosting(doc_id, tf));
        }
        
        inverted_index_.insert(term, posting_list);
    }
    
    while (std::getline(doc_file, line)) {
        std::istringstream iss(line);
        int doc_id;
        std::string url, title;
        
        iss >> doc_id;
        std::getline(iss, url, '\t');
        std::getline(iss, url, '\t');
        std::getline(iss, title);
        
        while (doc_urls_.size() <= static_cast<size_t>(doc_id)) {
            doc_urls_.push_back("");
            doc_titles_.push_back("");
            doc_lengths_.push_back(0);
        }
        
        doc_urls_[doc_id] = url;
        doc_titles_[doc_id] = title;
    }

    int doc_length = 0;
    size_t length_idx = 0;
    while (lengths_file.is_open() && (lengths_file >> doc_length)) {
        while (doc_lengths_.size() <= length_idx) {
            doc_lengths_.push_back(0);
        }
        doc_lengths_[length_idx] = doc_length;
        length_idx++;
    }
    
    vocab_file.close();
    index_file.close();
    doc_file.close();
    if (lengths_file.is_open()) {
        lengths_file.close();
    }
    
    std::cout << "Index loaded successfully!\n";
    std::cout << "Vocabulary size: " << inverted_index_.size() << "\n";
    std::cout << "Documents: " << doc_urls_.size() << "\n";
    
    return true;
}

DynamicArray<int> SearchEngine::intersect(const DynamicArray<int>& list1, const DynamicArray<int>& list2) {
    DynamicArray<int> result;

    size_t i = 0;
    size_t j = 0;
    while (i < list1.size() && j < list2.size()) {
        if (list1[i] == list2[j]) {
            result.push_back(list1[i]);
            i++;
            j++;
        } else if (list1[i] < list2[j]) {
            i++;
        } else {
            j++;
        }
    }

    return result;
}

DynamicArray<int> SearchEngine::union_lists(const DynamicArray<int>& list1, const DynamicArray<int>& list2) {
    DynamicArray<int> result;

    size_t i = 0;
    size_t j = 0;
    while (i < list1.size() || j < list2.size()) {
        if (i < list1.size() && (j >= list2.size() || list1[i] < list2[j])) {
            result.push_back(list1[i]);
            i++;
        } else if (j < list2.size() && (i >= list1.size() || list2[j] < list1[i])) {
            result.push_back(list2[j]);
            j++;
        } else {
            result.push_back(list1[i]);
            i++;
            j++;
        }
    }

    return result;
}

DynamicArray<int> SearchEngine::difference(const DynamicArray<int>& list1, const DynamicArray<int>& list2) {
    DynamicArray<int> result;

    size_t i = 0;
    size_t j = 0;
    while (i < list1.size()) {
        if (j >= list2.size()) {
            result.push_back(list1[i]);
            i++;
        } else if (list1[i] == list2[j]) {
            i++;
            j++;
        } else if (list1[i] < list2[j]) {
            result.push_back(list1[i]);
            i++;
        } else {
            j++;
        }
    }

    return result;
}

DynamicArray<int> SearchEngine::all_document_ids() const {
    DynamicArray<int> docs;
    for (size_t i = 0; i < doc_urls_.size(); ++i) {
        if (!doc_urls_[i].empty()) {
            docs.push_back(static_cast<int>(i));
        }
    }
    return docs;
}

DynamicArray<int> SearchEngine::posting_doc_ids(const std::string& stemmed_term) const {
    DynamicArray<int> docs;
    DynamicArray<SearchPosting> posting_list;
    if (!inverted_index_.find(stemmed_term, posting_list)) {
        return docs;
    }
    for (size_t i = 0; i < posting_list.size(); ++i) {
        docs.push_back(posting_list[i].doc_id);
    }
    return docs;
}

bool SearchEngine::contains_doc(const DynamicArray<SearchPosting>& posting_list, int doc_id) const {
    for (size_t i = 0; i < posting_list.size(); ++i) {
        if (posting_list[i].doc_id == doc_id) {
            return true;
        }
    }
    return false;
}

int SearchEngine::term_tf_for_doc(const DynamicArray<SearchPosting>& posting_list, int doc_id) const {
    for (size_t i = 0; i < posting_list.size(); ++i) {
        if (posting_list[i].doc_id == doc_id) {
            return posting_list[i].tf;
        }
    }
    return 0;
}

bool SearchEngine::is_operator_token(const std::string& token) const {
    return token == "and" || token == "or" || token == "not";
}

int SearchEngine::operator_precedence(const std::string& op) const {
    if (op == "not") return 3;
    if (op == "and") return 2;
    if (op == "or") return 1;
    return 0;
}

bool SearchEngine::is_left_associative(const std::string& op) const {
    return op != "not";
}

std::string SearchEngine::to_lower_ascii(const std::string& text) const {
    std::string lowered = text;
    for (size_t i = 0; i < lowered.size(); ++i) {
        lowered[i] = std::tolower(static_cast<unsigned char>(lowered[i]));
    }
    return lowered;
}

std::string SearchEngine::normalize_query_token(const std::string& token) const {
    if (token == "(" || token == ")") {
        return token;
    }

    std::string lowered = to_lower_ascii(token);
    if (lowered.empty()) {
        return lowered;
    }

    size_t left = 0;
    while (left < lowered.size() &&
           !std::isalnum(static_cast<unsigned char>(lowered[left])) &&
           lowered[left] != '\'') {
        left++;
    }

    size_t right = lowered.size();
    while (right > left &&
           !std::isalnum(static_cast<unsigned char>(lowered[right - 1])) &&
           lowered[right - 1] != '\'') {
        right--;
    }

    if (right <= left) {
        return "";
    }

    return lowered.substr(left, right - left);
}

DynamicArray<std::string> SearchEngine::to_rpn(const DynamicArray<std::string>& tokens) const {
    DynamicArray<std::string> output;
    DynamicArray<std::string> op_stack;

    for (size_t i = 0; i < tokens.size(); ++i) {
        const std::string& tok = tokens[i];
        if (tok.empty()) {
            continue;
        }

        if (tok == "(") {
            op_stack.push_back(tok);
            continue;
        }

        if (tok == ")") {
            while (!op_stack.empty() && op_stack[op_stack.size() - 1] != "(") {
                output.push_back(op_stack[op_stack.size() - 1]);
                op_stack.pop_back();
            }
            if (!op_stack.empty() && op_stack[op_stack.size() - 1] == "(") {
                op_stack.pop_back();
            }
            continue;
        }

        if (!is_operator_token(tok)) {
            output.push_back(tok);
            continue;
        }

        while (!op_stack.empty() && is_operator_token(op_stack[op_stack.size() - 1])) {
            const std::string& top = op_stack[op_stack.size() - 1];
            int top_prec = operator_precedence(top);
            int cur_prec = operator_precedence(tok);
            bool should_pop = top_prec > cur_prec ||
                              (top_prec == cur_prec && is_left_associative(tok));
            if (!should_pop) {
                break;
            }
            output.push_back(top);
            op_stack.pop_back();
        }
        op_stack.push_back(tok);
    }

    while (!op_stack.empty()) {
        if (op_stack[op_stack.size() - 1] != "(") {
            output.push_back(op_stack[op_stack.size() - 1]);
        }
        op_stack.pop_back();
    }

    return output;
}

DynamicArray<int> SearchEngine::eval_rpn(const DynamicArray<std::string>& rpn_tokens) {
    DynamicArray<DynamicArray<int>> stack;

    for (size_t i = 0; i < rpn_tokens.size(); ++i) {
        const std::string& tok = rpn_tokens[i];
        if (!is_operator_token(tok)) {
            std::string stem = stemmer_.stem(tok);
            stack.push_back(posting_doc_ids(stem));
            continue;
        }

        if (tok == "not") {
            if (stack.empty()) {
                continue;
            }
            DynamicArray<int> right = stack[stack.size() - 1];
            stack.pop_back();
            DynamicArray<int> left;
            if (!stack.empty()) {
                left = stack[stack.size() - 1];
                stack.pop_back();
            } else {
                left = all_document_ids();
            }
            stack.push_back(difference(left, right));
            continue;
        }

        if (stack.size() < 2) {
            continue;
        }

        DynamicArray<int> right = stack[stack.size() - 1];
        stack.pop_back();
        DynamicArray<int> left = stack[stack.size() - 1];
        stack.pop_back();

        if (tok == "and") {
            stack.push_back(intersect(left, right));
        } else if (tok == "or") {
            stack.push_back(union_lists(left, right));
        }
    }

    if (stack.empty()) {
        return DynamicArray<int>();
    }
    return stack[stack.size() - 1];
}

DynamicArray<std::string> SearchEngine::extract_query_terms(const DynamicArray<std::string>& tokens) {
    DynamicArray<std::string> unique_terms;
    for (size_t i = 0; i < tokens.size(); ++i) {
        const std::string& token = tokens[i];
        if (token.empty() || is_operator_token(token) || token == "(" || token == ")") {
            continue;
        }
        std::string stem = stemmer_.stem(token);
        if (stem.empty()) {
            continue;
        }

        bool already_added = false;
        for (size_t j = 0; j < unique_terms.size(); ++j) {
            if (unique_terms[j] == stem) {
                already_added = true;
                break;
            }
        }

        if (!already_added) {
            unique_terms.push_back(stem);
        }
    }
    return unique_terms;
}

double SearchEngine::compute_doc_score(int doc_id, const DynamicArray<std::string>& query_terms) const {
    if (doc_id < 0 || static_cast<size_t>(doc_id) >= doc_urls_.size()) {
        return -1.0;
    }

    const double total_docs = static_cast<double>(doc_urls_.size());
    std::string title_lower = to_lower_ascii(doc_titles_[doc_id]);
    std::string url_lower = to_lower_ascii(doc_urls_[doc_id]);
    double score = 0.0;

    for (size_t i = 0; i < query_terms.size(); ++i) {
        DynamicArray<SearchPosting> posting_list;
        if (!inverted_index_.find(query_terms[i], posting_list)) {
            continue;
        }
        int tf = term_tf_for_doc(posting_list, doc_id);
        if (tf <= 0) {
            continue;
        }

        double df = static_cast<double>(posting_list.size());
        double tf_weight = 1.0 + std::log(static_cast<double>(tf));
        double idf = std::log((total_docs + 1.0) / (df + 1.0)) + 1.0;
        score += tf_weight * idf;

        if (title_lower.find(query_terms[i]) != std::string::npos) {
            score += 0.35;
        }
        if (url_lower.find(query_terms[i]) != std::string::npos) {
            score += 0.15;
        }
    }

    if (static_cast<size_t>(doc_id) < doc_lengths_.size() && doc_lengths_[doc_id] > 0) {
        score /= std::sqrt(static_cast<double>(doc_lengths_[doc_id]));
    }

    return score;
}

DynamicArray<SearchResult> SearchEngine::search(const std::string& query, size_t* total_matches) {
    DynamicArray<SearchResult> results;

    std::string prepared_query;
    prepared_query.reserve(query.size() * 2);
    for (size_t i = 0; i < query.size(); ++i) {
        if (query[i] == '(' || query[i] == ')') {
            prepared_query += ' ';
            prepared_query += query[i];
            prepared_query += ' ';
        } else {
            prepared_query += query[i];
        }
    }

    DynamicArray<std::string> query_tokens;
    std::istringstream iss(prepared_query);
    std::string token;
    while (iss >> token) {
        std::string normalized = normalize_query_token(token);
        if (!normalized.empty()) {
            query_tokens.push_back(normalized);
        }
    }

    if (query_tokens.empty()) {
        if (total_matches) *total_matches = 0;
        return results;
    }

    DynamicArray<std::string> rpn = to_rpn(query_tokens);
    DynamicArray<int> doc_ids = eval_rpn(rpn);

    if (total_matches) *total_matches = doc_ids.size();
    DynamicArray<std::string> query_terms = extract_query_terms(query_tokens);

    DynamicArray<double> scores;
    for (size_t i = 0; i < doc_ids.size(); ++i) {
        scores.push_back(compute_doc_score(doc_ids[i], query_terms));
    }

    for (size_t i = 0; i < doc_ids.size(); ++i) {
        size_t best_idx = i;
        for (size_t j = i + 1; j < doc_ids.size(); ++j) {
            if (scores[j] > scores[best_idx] ||
                (scores[j] == scores[best_idx] && doc_ids[j] < doc_ids[best_idx])) {
                best_idx = j;
            }
        }
        if (best_idx != i) {
            int tmp_doc = doc_ids[i];
            doc_ids[i] = doc_ids[best_idx];
            doc_ids[best_idx] = tmp_doc;

            double tmp_score = scores[i];
            scores[i] = scores[best_idx];
            scores[best_idx] = tmp_score;
        }
    }

    for (size_t i = 0; i < doc_ids.size() && i < 100; ++i) {
        int doc_id = doc_ids[i];
        if (doc_id >= 0 && static_cast<size_t>(doc_id) < doc_urls_.size()) {
            results.push_back(SearchResult(doc_id, doc_urls_[doc_id], doc_titles_[doc_id]));
        }
    }

    return results;
}
