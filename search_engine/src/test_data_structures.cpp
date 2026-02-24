#include "data_structures.h"
#include <gtest/gtest.h>

TEST(DynamicArray, PushBackAndAccess) {
    DynamicArray<int> arr;
    EXPECT_EQ(arr.size(), 0);
    EXPECT_TRUE(arr.empty());

    arr.push_back(10);
    arr.push_back(20);
    arr.push_back(30);
    EXPECT_EQ(arr.size(), 3);
    EXPECT_EQ(arr[0], 10);
    EXPECT_EQ(arr[1], 20);
    EXPECT_EQ(arr[2], 30);
}

TEST(DynamicArray, PopBack) {
    DynamicArray<int> arr;
    arr.push_back(10);
    arr.push_back(20);
    arr.push_back(30);

    arr.pop_back();
    EXPECT_EQ(arr.size(), 2);
}

TEST(DynamicArray, Clear) {
    DynamicArray<int> arr;
    arr.push_back(10);
    arr.push_back(20);

    arr.clear();
    EXPECT_TRUE(arr.empty());
}

TEST(HashMap, InsertAndFind) {
    HashMap<std::string, int> map;
    EXPECT_EQ(map.size(), 0);
    EXPECT_TRUE(map.empty());

    map.insert("one", 1);
    map.insert("two", 2);
    map.insert("three", 3);
    EXPECT_EQ(map.size(), 3);

    int value;
    EXPECT_TRUE(map.find("one", value));
    EXPECT_EQ(value, 1);

    EXPECT_TRUE(map.find("two", value));
    EXPECT_EQ(value, 2);
}

TEST(HashMap, FindNonExistent) {
    HashMap<std::string, int> map;
    map.insert("one", 1);

    int value;
    EXPECT_FALSE(map.find("four", value));
}

TEST(HashMap, UpdateExisting) {
    HashMap<std::string, int> map;
    map.insert("one", 1);

    map.insert("one", 10);
    int value;
    EXPECT_TRUE(map.find("one", value));
    EXPECT_EQ(value, 10);
}

TEST(HashMap, Remove) {
    HashMap<std::string, int> map;
    map.insert("one", 1);
    map.insert("two", 2);
    map.insert("three", 3);

    map.remove("two");
    int value;
    EXPECT_FALSE(map.find("two", value));
    EXPECT_EQ(map.size(), 2);
}
