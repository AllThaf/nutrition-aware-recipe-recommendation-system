CREATE TABLE IF NOT EXISTS recipes (
    id            INTEGER PRIMARY KEY,
    name          TEXT NOT NULL,
    minutes       INTEGER,
    tags          TEXT[],
    ingredients   TEXT[],
    n_steps       INTEGER,
    steps         TEXT[],
    description   TEXT,
    nutrition     NUMERIC[],
    -- Index: [0]=calories [1]=total_fat_pdv [2]=sugar_pdv [3]=sodium_pdv
    --        [4]=protein_pdv [5]=sat_fat_pdv [6]=carbs_pdv
    n_ingredients INTEGER
);

CREATE TABLE IF NOT EXISTS interactions (
    user_id   INTEGER NOT NULL,
    recipe_id INTEGER NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
    rating    NUMERIC NOT NULL CHECK (rating >= 0 AND rating <= 5),
    date      DATE,
    review    TEXT,
    PRIMARY KEY (user_id, recipe_id)
);

-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_interactions_user   ON interactions(user_id);
CREATE INDEX IF NOT EXISTS idx_interactions_recipe ON interactions(recipe_id);
CREATE INDEX IF NOT EXISTS idx_recipes_name_fts    ON recipes USING gin(to_tsvector('english', name));
CREATE INDEX IF NOT EXISTS idx_recipes_tags        ON recipes USING gin(tags);
CREATE INDEX IF NOT EXISTS idx_recipes_ingredients ON recipes USING gin(ingredients);
