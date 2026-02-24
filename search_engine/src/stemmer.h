#ifndef STEMMER_H
#define STEMMER_H

#include <string>

class PorterStemmer {
private:
    std::string word_;
    int k_;
    int j_;
    
    bool is_consonant(int i) const;
    int measure() const;
    bool vowel_in_stem() const;
    bool double_consonant(int i) const;
    bool cvc(int i) const;
    bool ends(const std::string& s);
    void set_to(const std::string& s);
    void r(const std::string& s);
    void step1ab();
    void step1c();
    void step2();
    void step3();
    void step4();
    void step5();
    
public:
    PorterStemmer();
    std::string stem(const std::string& word);
};

#endif
