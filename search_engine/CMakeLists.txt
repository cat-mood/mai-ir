cmake_minimum_required(VERSION 3.14)
project(BooleanSearchEngine)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -O2 -Wall -Wextra")

include_directories(src)

add_executable(index_builder 
    src/index_builder_main.cpp
    src/index_builder.cpp
    src/tokenizer.cpp
    src/stemmer.cpp
    src/zipf_analysis.cpp
)

add_executable(search_cli 
    src/main_cli.cpp
    src/search_engine.cpp
    src/tokenizer.cpp
    src/stemmer.cpp
)

# --- Google Test ---
include(FetchContent)
FetchContent_Declare(
    googletest
    URL https://github.com/google/googletest/archive/refs/tags/v1.14.0.tar.gz
)
FetchContent_MakeAvailable(googletest)

enable_testing()
include(GoogleTest)

add_executable(test_data_structures
    src/test_data_structures.cpp
)
target_link_libraries(test_data_structures GTest::gtest_main)
gtest_discover_tests(test_data_structures)

add_executable(test_tokenizer
    src/test_tokenizer.cpp
    src/tokenizer.cpp
)
target_link_libraries(test_tokenizer GTest::gtest_main)
gtest_discover_tests(test_tokenizer)

add_executable(test_stemmer
    src/test_stemmer.cpp
    src/stemmer.cpp
)
target_link_libraries(test_stemmer GTest::gtest_main)
gtest_discover_tests(test_stemmer)
