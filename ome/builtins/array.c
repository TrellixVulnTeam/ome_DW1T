/*
    ome - Object Message Expressions
    Copyright (c) 2015-2016 Luke McCarthy <luke@iogopro.co.uk>
*/

#method Array size
{
    OME_Array *array = OME_untag_pointer(self);
    return OME_tag_integer(array->size);
}

#method Array at: index
{
    OME_Array *array = OME_untag_pointer(self);
    intptr_t u_index = OME_untag_signed(index);
    if (OME_get_tag(index) != OME_Tag_Small_Integer) {
        return OME_error(OME_Type_Error);
    }
    if (u_index < 0 || u_index >= array->size) {
        return OME_error(OME_Index_Error);
    }
    return array->elems[u_index];
}

#method Array each: block
{
    OME_LOCALS(2);
    OME_SAVE_LOCAL(0, self);
    OME_SAVE_LOCAL(1, block);
    OME_Method_1 item_method = @lookup("item:")(block);
    if (!item_method) {
        OME_ERROR(Not_Understood);
    }
    OME_Array *array = OME_untag_pointer(self);
    size_t size = array->size;
    for (size_t index = 0; index < size; index++) {
        OME_RETURN_ERROR(item_method(block, array->elems[index]));
        OME_LOAD_LOCAL(0, self);
        OME_LOAD_LOCAL(1, block);
        array = OME_untag_pointer(self);
    }
    OME_RETURN(OME_Empty);
}

#method Array enumerate: block
{
    OME_LOCALS(2);
    OME_SAVE_LOCAL(0, self);
    OME_SAVE_LOCAL(1, block);
    OME_Method_2 item_index_method = @lookup("item:index:")(block);
    if (!item_index_method) {
        OME_ERROR(Not_Understood);
    }
    OME_Array *array = OME_untag_pointer(self);
    size_t size = array->size;
    for (size_t index = 0; index < size; index++) {
        OME_Value t_index = OME_tag_integer(index);
        OME_RETURN_ERROR(item_index_method(block, array->elems[index], t_index));
        OME_LOAD_LOCAL(0, self);
        OME_LOAD_LOCAL(1, block);
        array = OME_untag_pointer(self);
    }
    OME_RETURN(OME_Empty);
}

#method Array + rhs
{
    if (OME_get_tag(rhs) != OME_Tag_Array) {
        return OME_error(OME_Type_Error);
    }
    size_t lsize = OME_untag_array(self)->size;
    size_t rsize = OME_untag_array(rhs)->size;
    if (rsize == 0) {
        return self;
    }
    if (lsize == 0) {
        return rhs;
    }
    size_t size = lsize + rsize;
    if (size > UINT32_MAX) {
        return OME_error(OME_Size_Error);
    }
    OME_LOCALS(2);
    OME_SAVE_LOCAL(0, self);
    OME_SAVE_LOCAL(1, rhs);
    OME_Array *dst = OME_allocate_array(size);
    OME_LOAD_LOCAL(0, self);
    OME_LOAD_LOCAL(1, rhs);
    OME_Array *src1 = OME_untag_pointer(self);
    OME_Array *src2 = OME_untag_pointer(rhs);
    memcpy(dst->elems, src1->elems, src1->size * sizeof(OME_Value));
    memcpy(dst->elems + src1->size, src2->elems, src2->size * sizeof(OME_Value));
    OME_RETURN(OME_tag_pointer(OME_Tag_Array, dst));
}

static int OME_compare_values(const void *pa, const void *pb)
{
    OME_Value a = *(OME_Value *) pa;
    OME_Value b = *(OME_Value *) pb;
    if (OME_equal(a, b) || OME_is_true(OME_message___EQ(a, b))) {
        return 0;
    }
    return OME_is_true(OME_message___LT(a, b)) ? -1 : 1;
}

#method Array sorted
{
    (void) @message("==");
    (void) @message("<");
    OME_Array *src = OME_untag_pointer(self);
    size_t size = src->size;
    OME_Array *tmp = malloc(sizeof(OME_Value) * size);
    memcpy(tmp, src->elems, size * sizeof(OME_Value));
    qsort(tmp, size, sizeof(OME_Value), OME_compare_values);
    OME_Array *dst = OME_allocate_array(size);
    memcpy(dst->elems, tmp, sizeof(OME_Value) * size);
    free(tmp);
    return OME_tag_pointer(OME_Tag_Array, dst);
}
