#pragma once
#ifndef _UTIL_H
#define _UTIL_H


 //Linked List
#define LINKED_LIST_ENTRY(TYPE) \
	TYPE *_next

#define LINKED_LIST(TYPE) \
	TYPE *_head, *_tail

#define LINKED_LIST_HEAD(ROOT) \
	ROOT->_head

#define LINKED_LIST_TAIL(ROOT) \
	ROOT->_tail

#define LINKED_LIST_NEXT(ENTRY) \
	ENTRY->_next

#define LINKED_LIST_INIT(TYPE, ROOT) \
	LINKED_LIST_HEAD(ROOT) = (TYPE*)NULL; LINKED_LIST_TAIL(ROOT) = (TYPE*)NULL

#define LINKED_LIST_INSERT_HEAD(TYPE, ROOT, PDATA) \
	do { \
		if(LINKED_LIST_HEAD(ROOT) == NULL) { \
			LINKED_LIST_HEAD(ROOT) = LINKED_LIST_TAIL(ROOT) = PDATA; \
		} else { \
			TYPE *tmp; \
			tmp = LINKED_LIST_HEAD(ROOT); \
			LINKED_LIST_HEAD(ROOT) = PDATA; \
			LINKED_LIST_NEXT(ROOT->_head)= tmp; \
		} \
	} while(0)

#define LINKED_LIST_INSERT_TAIL(TYPE, ROOT, PDATA) \
	do { \
		if(LINKED_LIST_TAIL(ROOT) == NULL || LINKED_LIST_TAIL(ROOT) == NULL) { \
			LINKED_LIST_HEAD(ROOT) = LINKED_LIST_TAIL(ROOT) = PDATA; \
			LINKED_LIST_NEXT(PDATA) = NULL; \
		} else { \
			LINKED_LIST_TAIL(ROOT)->_next = PDATA; \
			LINKED_LIST_NEXT(PDATA) = NULL; \
			LINKED_LIST_TAIL(ROOT) = PDATA; \
		} \
	} while(0)

#define LINKED_LIST_FOREACH(VAR, ROOT) \
	for(VAR = LINKED_LIST_HEAD(ROOT); VAR; VAR = LINKED_LIST_NEXT(VAR))

#define LINKED_LIST_DESTROY(TYPE, ROOT, DEALLOC) \
	do { \
		TYPE *current, *prev; \
		for(current=LINKED_LIST_HEAD(ROOT); current != NULL;) { \
			prev = current; \
			current = LINKED_LIST_NEXT(current); \
			if(DEALLOC != NULL) DEALLOC(prev); \
		} \
		ROOT->_head = ROOT->_tail = NULL; \
	} while(0)

 //Vector
#define VECTOR_DEFINE(NAME, TYPE) \
struct _vector_##NAME \
{ \
	TYPE *list; \
	unsigned int size; \
	unsigned int max; \
	const unsigned int growth; \
};\
\
int _vector_##NAME##_insert(struct _vector_##NAME *vector, TYPE elem) \
{ \
	if(vector->size + 1 >= vector->max) { \
		vector->max = vector->max + vector->growth; \
		vector->list = (TYPE*)realloc(vector->list, sizeof(TYPE) * vector->max); \
	} \
\
	vector->list[vector->size] = elem; \
\
	return (vector->size++); \
} \
\
TYPE* _vector_##NAME##_at(struct _vector_##NAME *vector, unsigned int index) \
{ \
	if(index > vector->max) return NULL; \
	return &vector->list[index]; \
}

#define VECTOR_CREATE(NAME, ID, GROWTH) struct _vector_##NAME ID = {NULL, 0, 0, GROWTH}
#define VECTOR_PUSHBACK(NAME, ID, ELEM) _vector_##NAME##_insert(ID, ELEM)
#define VECTOR_AT(NAME, ID, IDX) _vector_##NAME##_at(ID, IDX)
#define VECTOR_SIZE(ID) ID->size
#define VECTOR_MAX(ID) ID->max
#define VECTOR_DESTROY(ID) free(ID.list)

#ifndef HEXDUMP_COLS
#define HEXDUMP_COLS 8
#endif

int round_int(double value);
unsigned int round_uint(double value);
int log2_int(int value);
int bitrev(int value, int bits);

char do_amcc_inp (int card_num, unsigned int address);
int do_amcc_outp (int card_num, unsigned int address, char data);
int do_amcc_outp_old (int card_num, unsigned int address, int data);

char *my_strcat (const char *a, const char *b);
char *my_sprintf (const char *format, ...);


#endif /* #ifndef _UTIL_H */
