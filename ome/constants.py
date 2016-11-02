# ome - Object Message Expressions
# Copyright (c) 2015-2016 Luke McCarthy <luke@iogopro.co.uk>. All rights reserved.

NUM_BITS = 64
NUM_TAG_BITS = 20
NUM_DATA_BITS = NUM_BITS - NUM_TAG_BITS
NUM_EXPONENT_BITS = 8
NUM_SIGNIFICAND_BITS = NUM_DATA_BITS - NUM_EXPONENT_BITS
ERROR_BIT = 1 << (NUM_TAG_BITS - 1)

HEAP_ALIGNMENT_SHIFT = 4
HEAP_ALIGNMENT = 1 << HEAP_ALIGNMENT_SHIFT
HEAP_SIZE_BITS = 10  # 2^10-1 = 1023 slots (~8 KB)
MAX_HEAP_OBJECT_SIZE = 2**HEAP_SIZE_BITS - 1

MAX_TAG = 2**(NUM_TAG_BITS-1) - 2  # Highest bit of tag is error bit
MIN_CONSTANT_TAG = 2**NUM_TAG_BITS
MAX_CONSTANT_TAG = 2**32 - MIN_CONSTANT_TAG - 1

MIN_SMALL_INTEGER = -2**(NUM_DATA_BITS-1)
MAX_SMALL_INTEGER = 2**(NUM_DATA_BITS-1) - 1
MIN_EXPONENT = -2**(NUM_EXPONENT_BITS-1)
MAX_EXPONENT = 2**(NUM_EXPONENT_BITS-1) - 1
MIN_SIGNIFICAND = -2**(NUM_SIGNIFICAND_BITS-1)
MAX_SIGNIFICAND = 2**(NUM_SIGNIFICAND_BITS-1) - 1

MASK_TAG = (1 << NUM_TAG_BITS) - 1
MASK_DATA = (1 << NUM_DATA_BITS) - 1
MASK_EXPONENT = (1 << NUM_EXPONENT_BITS) - 1
MASK_SIGNIFICAND = (1 << NUM_SIGNIFICAND_BITS) - 1
