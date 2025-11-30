"""Dictionary API routes.

Combines all dictionary-related routers.
"""

from fastapi import APIRouter

from api.routes.dictionary import definitions, examples, relations, tags, words

router = APIRouter(prefix="/v1/dictionary", tags=["dictionary"])

# Include sub-routers
router.include_router(words.router)
router.include_router(definitions.router)
router.include_router(examples.router)
router.include_router(tags.router)
router.include_router(relations.router)
