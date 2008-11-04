from django import template
from settings import RESULTS_ON_PAGE
register = template.Library()

LEADING_PAGE_RANGE_DISPLAYED = TRAILING_PAGE_RANGE_DISPLAYED = 10
LEADING_PAGE_RANGE = TRAILING_PAGE_RANGE = 8
NUM_PAGES_OUTSIDE_RANGE = 2
ADJACENT_PAGES = 4

def paginator(context):
    in_leading_range = in_trailing_range = False
    pages_outside_leading_range = pages_outside_trailing_range = []

    if (context["result"].paginator.num_pages <= LEADING_PAGE_RANGE_DISPLAYED + NUM_PAGES_OUTSIDE_RANGE + 1):
        in_leading_range = in_trailing_range = True
        page_numbers = [n for n in range(1, context["result"].paginator.num_pages + 1) if n > 0 and n <= context["result"].paginator.num_pages]
    elif (context["result"].number <= LEADING_PAGE_RANGE):
        in_leading_range = True
        page_numbers = [n for n in range(1, LEADING_PAGE_RANGE_DISPLAYED + 1) if n > 0 and n <= context["result"].paginator.num_pages]
        pages_outside_leading_range = [n + context["result"].paginator.num_pages for n in range(0, -NUM_PAGES_OUTSIDE_RANGE, -1)]
    elif (context["result"].number > context["result"].paginator.num_pages - TRAILING_PAGE_RANGE):
        in_trailing_range = True
        page_numbers = [n for n in range(context["result"].paginator.num_pages - TRAILING_PAGE_RANGE_DISPLAYED + 1, context["result"].paginator.num_pages + 1) if n > 0 and n <= context["result"].paginator.num_pages]
        pages_outside_trailing_range = [n + 1 for n in range(0, NUM_PAGES_OUTSIDE_RANGE)]
    else:
        page_numbers = [n for n in range(context["result"].number - ADJACENT_PAGES, context["result"].number + ADJACENT_PAGES + 1) if n > 0 and n <= context["result"].paginator.num_pages]
        pages_outside_leading_range = [n + context["result"].paginator.num_pages for n in range(0, -NUM_PAGES_OUTSIDE_RANGE, -1)]
        pages_outside_trailing_range = [n + 1 for n in range(0, NUM_PAGES_OUTSIDE_RANGE)]
    return {
        "previous": context["result"].previous_page_number(),
        "has_previous": context["result"].has_previous(),
        "next": context["result"].next_page_number(),
        "has_next": context["result"].has_next(),
        "results_per_page": RESULTS_ON_PAGE,
        "page": context["result"].number,
        "pages": context["result"].paginator.num_pages,
        "page_numbers": page_numbers,
        "in_leading_range" : in_leading_range,
        "in_trailing_range" : in_trailing_range,
        "pages_outside_leading_range": pages_outside_leading_range,
        "pages_outside_trailing_range": pages_outside_trailing_range,
        "args": context.get("args"),
        "title": context.get("title"),
    }

register.inclusion_tag("paginator.htm", takes_context=True)(paginator)
