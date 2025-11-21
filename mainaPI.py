import os
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, ConfigDict, Field, model_validator


load_dotenv()

DB_HOST = os.getenv("POSTGRES_HOST")
DB_PORT = os.getenv("POSTGRES_PORT")
DB_USER = os.getenv("POSTGRES_USER")
DB_NAME = os.getenv("POSTGRES_DB")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")


class RouteRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    PassingCityName: bool = Field(default=False, description="When true, treat starting/destination values as city names.")
    starting_id: Optional[int] = Field(default=None, description="Identifier of the starting city.")
    starting_name: Optional[str] = Field(default=None, description="City name of the starting location.")
    destination_id: Optional[int] = Field(default=None, description="Identifier of the destination city.")
    destination_name: Optional[str] = Field(default=None, description="City name of the destination.")

    @model_validator(mode="after")
    def _ensure_inputs(self) -> "RouteRequest":
        has_start = self.starting_id is not None or (self.starting_name is not None and self.starting_name.strip())
        has_dest = self.destination_id is not None or (self.destination_name is not None and self.destination_name.strip())
        if not has_start or not has_dest:
            raise ValueError("Provide either ID or name for both starting and destination locations.")
        return self


def _get_db_connection():
    if not all([DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME]):
        raise HTTPException(status_code=500, detail="Database environment variables are not fully configured.")

    try:
        return psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            cursor_factory=RealDictCursor,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {exc}")


def _decimal_to_float(record: Dict[str, Any]) -> Dict[str, Any]:
    converted = {}
    for key, value in record.items():
        if isinstance(value, Decimal):
            converted[key] = float(value)
        else:
            converted[key] = value
    return converted


def _resolve_city_identifiers(conn, name: Optional[str], identifier: Optional[int], label: str) -> Tuple[int, str]:
    if identifier is not None and name is not None:
        return identifier, name

    if identifier is not None:
        with conn.cursor() as cur:
            cur.execute("SELECT city_name FROM public.destinations WHERE id = %s LIMIT 1;", (identifier,))
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail=f"No city found for {label} id {identifier}.")
            return identifier, row["city_name"]

    assert name is not None  # Guaranteed by validation
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM public.destinations WHERE city_name = %s ORDER BY id LIMIT 1;", (name,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=f"No city found matching {label} name '{name}'.")
        return row["id"], name


def _run_query(conn, query: str, params: Tuple[Any, ...]) -> List[Dict[str, Any]]:
    try:
        with conn.cursor() as cur:
            cur.execute(query, params)
            results = cur.fetchall()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Query execution failed: {exc}")

    return [_decimal_to_float(dict(row)) for row in results]


app = FastAPI(title="Route General Report API")


@app.post("/route-general-report")
def get_route_general_report(payload: RouteRequest) -> Dict[str, Any]:
    conn = _get_db_connection()
    try:
        start_id, start_name = _resolve_city_identifiers(conn, payload.starting_name, payload.starting_id, "starting")
        dest_id, dest_name = _resolve_city_identifiers(conn, payload.destination_name, payload.destination_id, "destination")

        if payload.PassingCityName:
            query = """
                SELECT

                    o.enlistment_hour,
                    sd.city_name AS starting_city,
                    dd.city_name AS destination_city,
                    ROUND(AVG(o.trailer_avg_price_per_km), 4)             AS avg_trailer_price,
                    ROUND(AVG(o.vehicle_up_to_3_5_t_avg_price_per_km), 4) AS avg_3_5t_price,
                    ROUND(AVG(o.vehicle_up_to_12_t_avg_price_per_km), 4)  AS avg_12t_price
                FROM public.offers AS o
                JOIN public.destinations AS sd ON sd.id = o.starting_id
                JOIN public.destinations AS dd ON dd.id = o.destination_id
                WHERE sd.city_name = %s
                  AND dd.city_name = %s
                GROUP BY
                    o.enlistment_hour,
                    sd.city_name,
                    dd.city_name
                HAVING
                    AVG(o.trailer_avg_price_per_km) IS NOT NULL
                OR AVG(o.vehicle_up_to_3_5_t_avg_price_per_km) IS NOT NULL
                OR AVG(o.vehicle_up_to_12_t_avg_price_per_km) IS NOT NULL
                ORDER BY  o.enlistment_hour;
            """
            params = (start_name, dest_name)
        else:
            query = """
                SELECT
                    o.enlistment_hour,
                    ROUND(AVG(o.trailer_avg_price_per_km), 4)             AS avg_trailer_price,
                    ROUND(AVG(o.vehicle_up_to_3_5_t_avg_price_per_km), 4) AS avg_3_5t_price,
                    ROUND(AVG(o.vehicle_up_to_12_t_avg_price_per_km), 4)  AS avg_12t_price
                FROM public.offers AS o
                WHERE o.starting_id = %s
                  AND o.destination_id = %s
                GROUP BY  o.enlistment_hour
                HAVING
                    AVG(o.trailer_avg_price_per_km) IS NOT NULL
                OR AVG(o.vehicle_up_to_3_5_t_avg_price_per_km) IS NOT NULL
                OR AVG(o.vehicle_up_to_12_t_avg_price_per_km) IS NOT NULL
                ORDER BY  o.enlistment_hour;
            """
            params = (start_id, dest_id)

        data = _run_query(conn, query, params)
    finally:
        conn.close()

    return {
        "query_mode": "city_name" if payload.PassingCityName else "id",
        "start": {"id": start_id, "name": start_name},
        "destination": {"id": dest_id, "name": dest_name},
        "rows": jsonable_encoder(data),
        "row_count": len(data),
    }


@app.get("/health")
def health_check() -> Dict[str, str]:
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)

