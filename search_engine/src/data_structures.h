#ifndef DATA_STRUCTURES_H
#define DATA_STRUCTURES_H

#include <cstddef>
#include <cstring>
#include <stdexcept>

template<typename T>
class DynamicArray {
private:
    T* data_;
    size_t size_;
    size_t capacity_;
    
    void resize(size_t new_capacity) {
        T* new_data = new T[new_capacity];
        for (size_t i = 0; i < size_; ++i) {
            new_data[i] = data_[i];
        }
        delete[] data_;
        data_ = new_data;
        capacity_ = new_capacity;
    }
    
public:
    DynamicArray() : data_(nullptr), size_(0), capacity_(0) {}
    
    explicit DynamicArray(size_t initial_capacity) 
        : data_(new T[initial_capacity]), size_(0), capacity_(initial_capacity) {}
    
    ~DynamicArray() {
        delete[] data_;
    }
    
    DynamicArray(const DynamicArray& other) 
        : data_(new T[other.capacity_]), size_(other.size_), capacity_(other.capacity_) {
        for (size_t i = 0; i < size_; ++i) {
            data_[i] = other.data_[i];
        }
    }
    
    DynamicArray& operator=(const DynamicArray& other) {
        if (this != &other) {
            delete[] data_;
            capacity_ = other.capacity_;
            size_ = other.size_;
            data_ = new T[capacity_];
            for (size_t i = 0; i < size_; ++i) {
                data_[i] = other.data_[i];
            }
        }
        return *this;
    }
    
    void push_back(const T& value) {
        if (size_ == capacity_) {
            size_t new_capacity = capacity_ == 0 ? 8 : capacity_ * 2;
            resize(new_capacity);
        }
        data_[size_++] = value;
    }
    
    void pop_back() {
        if (size_ > 0) {
            --size_;
        }
    }
    
    T& operator[](size_t index) {
        return data_[index];
    }
    
    const T& operator[](size_t index) const {
        return data_[index];
    }
    
    T& at(size_t index) {
        if (index >= size_) {
            throw std::out_of_range("Index out of range");
        }
        return data_[index];
    }
    
    const T& at(size_t index) const {
        if (index >= size_) {
            throw std::out_of_range("Index out of range");
        }
        return data_[index];
    }
    
    size_t size() const { return size_; }
    size_t capacity() const { return capacity_; }
    bool empty() const { return size_ == 0; }
    
    T* data() { return data_; }
    const T* data() const { return data_; }
    
    void clear() {
        size_ = 0;
    }
    
    void reserve(size_t new_capacity) {
        if (new_capacity > capacity_) {
            resize(new_capacity);
        }
    }
    
    T* begin() { return data_; }
    T* end() { return data_ + size_; }
    const T* begin() const { return data_; }
    const T* end() const { return data_ + size_; }
};

template<typename K, typename V>
class HashMap {
private:
    struct Entry {
        K key;
        V value;
        bool occupied;
        bool deleted;
        
        Entry() : occupied(false), deleted(false) {}
    };
    
    Entry* table_;
    size_t capacity_;
    size_t size_;
    
    size_t hash(const K& key) const {
        std::hash<K> hasher;
        return hasher(key) % capacity_;
    }
    
    void rehash(size_t new_capacity) {
        Entry* old_table = table_;
        size_t old_capacity = capacity_;
        
        table_ = new Entry[new_capacity];
        capacity_ = new_capacity;
        size_ = 0;
        
        for (size_t i = 0; i < old_capacity; ++i) {
            if (old_table[i].occupied && !old_table[i].deleted) {
                insert(old_table[i].key, old_table[i].value);
            }
        }
        
        delete[] old_table;
    }
    
public:
    HashMap() : table_(new Entry[16]), capacity_(16), size_(0) {}
    
    explicit HashMap(size_t initial_capacity) 
        : table_(new Entry[initial_capacity]), capacity_(initial_capacity), size_(0) {}
    
    ~HashMap() {
        delete[] table_;
    }
    
    HashMap(const HashMap& other) 
        : table_(new Entry[other.capacity_]), capacity_(other.capacity_), size_(other.size_) {
        for (size_t i = 0; i < capacity_; ++i) {
            table_[i] = other.table_[i];
        }
    }
    
    HashMap& operator=(const HashMap& other) {
        if (this != &other) {
            delete[] table_;
            capacity_ = other.capacity_;
            size_ = other.size_;
            table_ = new Entry[capacity_];
            for (size_t i = 0; i < capacity_; ++i) {
                table_[i] = other.table_[i];
            }
        }
        return *this;
    }
    
    void insert(const K& key, const V& value) {
        if (static_cast<double>(size_) / capacity_ > 0.7) {
            rehash(capacity_ * 2);
        }
        
        size_t index = hash(key);
        size_t original_index = index;
        
        while (table_[index].occupied && !table_[index].deleted) {
            if (table_[index].key == key) {
                table_[index].value = value;
                return;
            }
            index = (index + 1) % capacity_;
            if (index == original_index) {
                rehash(capacity_ * 2);
                insert(key, value);
                return;
            }
        }
        
        table_[index].key = key;
        table_[index].value = value;
        table_[index].occupied = true;
        table_[index].deleted = false;
        ++size_;
    }
    
    bool find(const K& key, V& value) const {
        size_t index = hash(key);
        size_t original_index = index;
        
        while (table_[index].occupied) {
            if (!table_[index].deleted && table_[index].key == key) {
                value = table_[index].value;
                return true;
            }
            index = (index + 1) % capacity_;
            if (index == original_index) {
                break;
            }
        }
        return false;
    }
    
    bool contains(const K& key) const {
        V dummy;
        return find(key, dummy);
    }
    
    V& operator[](const K& key) {
        size_t index = hash(key);
        size_t original_index = index;
        
        while (table_[index].occupied) {
            if (!table_[index].deleted && table_[index].key == key) {
                return table_[index].value;
            }
            index = (index + 1) % capacity_;
            if (index == original_index) {
                break;
            }
        }
        
        insert(key, V());
        return (*this)[key];
    }
    
    void remove(const K& key) {
        size_t index = hash(key);
        size_t original_index = index;
        
        while (table_[index].occupied) {
            if (!table_[index].deleted && table_[index].key == key) {
                table_[index].deleted = true;
                --size_;
                return;
            }
            index = (index + 1) % capacity_;
            if (index == original_index) {
                break;
            }
        }
    }
    
    size_t size() const { return size_; }
    bool empty() const { return size_ == 0; }
    
    class Iterator {
    private:
        Entry* table_;
        size_t capacity_;
        size_t current_;
        
        void advance() {
            while (current_ < capacity_ && 
                   (!table_[current_].occupied || table_[current_].deleted)) {
                ++current_;
            }
        }
        
    public:
        Iterator(Entry* table, size_t capacity, size_t start) 
            : table_(table), capacity_(capacity), current_(start) {
            advance();
        }
        
        bool operator!=(const Iterator& other) const {
            return current_ != other.current_;
        }
        
        Iterator& operator++() {
            ++current_;
            advance();
            return *this;
        }
        
        K& key() { return table_[current_].key; }
        V& value() { return table_[current_].value; }
    };
    
    Iterator begin() { return Iterator(table_, capacity_, 0); }
    Iterator end() { return Iterator(table_, capacity_, capacity_); }
};

#endif
