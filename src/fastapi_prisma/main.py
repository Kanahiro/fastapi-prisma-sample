from contextlib import asynccontextmanager

from fastapi import FastAPI
from prisma import Prisma
from pydantic import BaseModel, Field
from geojson_pydantic import Feature, FeatureCollection

prisma = Prisma()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await prisma.connect()
    yield
    await prisma.disconnect()


app = FastAPI(lifespan=lifespan)


@app.get("/health")
def index():
    return {"status": "ok"}


@app.post("/{theme_id}/features")
async def post_feature(theme_id: str, feature: Feature):
    return await prisma.feature.create(
        data={"themeId": theme_id, **feature.model_dump()}
    )


@app.get("/{theme_id}/features")
async def get_features(theme_id: str):
    _features = await prisma.feature.find_many(where={"themeId": theme_id})
    return FeatureCollection(
        type="FeatureCollection",
        features=[
            Feature(
                type="Feature",
                **{
                    "geometry": {
                        "type": "Point",
                        "coordinates": [feature.longitude, feature.latitude],
                    },
                    "properties": {
                        "name": feature.name,
                    },
                },
            )
            for feature in _features
        ],
    )


class Theme(BaseModel):
    name: str = Field(str, description="Theme name", length=100)


@app.post("/themes")
async def post_theme(theme: Theme):
    return await prisma.theme.create(data=theme.model_dump())


@app.get("/themes")
async def get_themes():
    return await prisma.theme.find_many()
