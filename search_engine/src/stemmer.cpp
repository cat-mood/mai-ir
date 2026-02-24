#include "stemmer.h"
#include <cctype>

PorterStemmer::PorterStemmer() : k_(0), j_(0) {}

bool PorterStemmer::is_consonant(int i) const {
    char ch = word_[i];
    if (ch == 'a' || ch == 'e' || ch == 'i' || ch == 'o' || ch == 'u') {
        return false;
    }
    if (ch == 'y') {
        return (i == 0) ? true : !is_consonant(i - 1);
    }
    return true;
}

int PorterStemmer::measure() const {
    int n = 0;
    int i = 0;
    while (true) {
        if (i > j_) return n;
        if (!is_consonant(i)) break;
        i++;
    }
    i++;
    while (true) {
        while (true) {
            if (i > j_) return n;
            if (is_consonant(i)) break;
            i++;
        }
        i++;
        n++;
        while (true) {
            if (i > j_) return n;
            if (!is_consonant(i)) break;
            i++;
        }
        i++;
    }
}

bool PorterStemmer::vowel_in_stem() const {
    for (int i = 0; i <= j_; i++) {
        if (!is_consonant(i)) return true;
    }
    return false;
}

bool PorterStemmer::double_consonant(int i) const {
    if (i < 1) return false;
    if (word_[i] != word_[i - 1]) return false;
    return is_consonant(i);
}

bool PorterStemmer::cvc(int i) const {
    if (i < 2 || !is_consonant(i) || is_consonant(i - 1) || !is_consonant(i - 2)) {
        return false;
    }
    char ch = word_[i];
    if (ch == 'w' || ch == 'x' || ch == 'y') return false;
    return true;
}

bool PorterStemmer::ends(const std::string& s) {
    int length = s.length();
    if (s[length - 1] != word_[k_]) return false;
    if (length > k_ + 1) return false;
    if (word_.substr(k_ - length + 1, length) != s) return false;
    j_ = k_ - length;
    return true;
}

void PorterStemmer::set_to(const std::string& s) {
    int length = s.length();
    word_.replace(j_ + 1, k_ - j_, s);
    k_ = j_ + length;
}

void PorterStemmer::r(const std::string& s) {
    if (measure() > 0) set_to(s);
}

void PorterStemmer::step1ab() {
    if (word_[k_] == 's') {
        if (ends("sses")) k_ -= 2;
        else if (ends("ies")) set_to("i");
        else if (word_[k_ - 1] != 's') k_--;
    }
    if (ends("eed")) {
        if (measure() > 0) k_--;
    } else if ((ends("ed") || ends("ing")) && vowel_in_stem()) {
        k_ = j_;
        if (ends("at")) set_to("ate");
        else if (ends("bl")) set_to("ble");
        else if (ends("iz")) set_to("ize");
        else if (double_consonant(k_)) {
            k_--;
            char ch = word_[k_];
            if (ch == 'l' || ch == 's' || ch == 'z') k_++;
        } else if (measure() == 1 && cvc(k_)) {
            set_to("e");
        }
    }
}

void PorterStemmer::step1c() {
    if (ends("y") && vowel_in_stem()) {
        word_[k_] = 'i';
    }
}

void PorterStemmer::step2() {
    if (k_ == 0) return;
    switch (word_[k_ - 1]) {
        case 'a':
            if (ends("ational")) { r("ate"); break; }
            if (ends("tional")) { r("tion"); break; }
            break;
        case 'c':
            if (ends("enci")) { r("ence"); break; }
            if (ends("anci")) { r("ance"); break; }
            break;
        case 'e':
            if (ends("izer")) { r("ize"); break; }
            break;
        case 'l':
            if (ends("bli")) { r("ble"); break; }
            if (ends("alli")) { r("al"); break; }
            if (ends("entli")) { r("ent"); break; }
            if (ends("eli")) { r("e"); break; }
            if (ends("ousli")) { r("ous"); break; }
            break;
        case 'o':
            if (ends("ization")) { r("ize"); break; }
            if (ends("ation")) { r("ate"); break; }
            if (ends("ator")) { r("ate"); break; }
            break;
        case 's':
            if (ends("alism")) { r("al"); break; }
            if (ends("iveness")) { r("ive"); break; }
            if (ends("fulness")) { r("ful"); break; }
            if (ends("ousness")) { r("ous"); break; }
            break;
        case 't':
            if (ends("aliti")) { r("al"); break; }
            if (ends("iviti")) { r("ive"); break; }
            if (ends("biliti")) { r("ble"); break; }
            break;
        case 'g':
            if (ends("logi")) { r("log"); break; }
            break;
    }
}

void PorterStemmer::step3() {
    switch (word_[k_]) {
        case 'e':
            if (ends("icate")) { r("ic"); break; }
            if (ends("ative")) { r(""); break; }
            if (ends("alize")) { r("al"); break; }
            break;
        case 'i':
            if (ends("iciti")) { r("ic"); break; }
            break;
        case 'l':
            if (ends("ical")) { r("ic"); break; }
            if (ends("ful")) { r(""); break; }
            break;
        case 's':
            if (ends("ness")) { r(""); break; }
            break;
    }
}

void PorterStemmer::step4() {
    switch (word_[k_ - 1]) {
        case 'a':
            if (ends("al")) break; return;
        case 'c':
            if (ends("ance")) break;
            if (ends("ence")) break; return;
        case 'e':
            if (ends("er")) break; return;
        case 'i':
            if (ends("ic")) break; return;
        case 'l':
            if (ends("able")) break;
            if (ends("ible")) break; return;
        case 'n':
            if (ends("ant")) break;
            if (ends("ement")) break;
            if (ends("ment")) break;
            if (ends("ent")) break; return;
        case 'o':
            if (ends("ion") && j_ >= 0 && (word_[j_] == 's' || word_[j_] == 't')) break;
            if (ends("ou")) break; return;
        case 's':
            if (ends("ism")) break; return;
        case 't':
            if (ends("ate")) break;
            if (ends("iti")) break; return;
        case 'u':
            if (ends("ous")) break; return;
        case 'v':
            if (ends("ive")) break; return;
        case 'z':
            if (ends("ize")) break; return;
        default:
            return;
    }
    if (measure() > 1) k_ = j_;
}

void PorterStemmer::step5() {
    j_ = k_;
    if (word_[k_] == 'e') {
        int a = measure();
        if (a > 1 || (a == 1 && !cvc(k_ - 1))) k_--;
    }
    if (word_[k_] == 'l' && double_consonant(k_) && measure() > 1) k_--;
}

std::string PorterStemmer::stem(const std::string& word) {
    word_ = word;
    k_ = word_.length() - 1;
    
    if (k_ <= 1) return word_;
    
    step1ab();
    step1c();
    step2();
    step3();
    step4();
    step5();
    
    return word_.substr(0, k_ + 1);
}
