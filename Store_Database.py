import streamlit as st
import psycopg2
import pandas as pd

st.set_page_config(page_title="Identifier Mapping Tool", layout="centered")
st.title("🔗 Identifier Mapping Entry Tool")

# -----------------------------------
# 1. Manual Entry Form
# -----------------------------------
with st.form("entry_form"):
    source = st.text_input("Source Database", "UniProt")
    target = st.text_input("Target Database", "Ensembl")
    id_type = st.text_input("Identifier Type", "Protein")
    src_format = st.text_input("Source Identifier Format", "UniProtKB Accession")
    tgt_format = st.text_input("Target Identifier Format", "Ensembl Protein ID")
    url = st.text_input("Translation Service URL", "https://rest.ensembl.org/xrefs/id/")
    notes = st.text_area("Notes", "Supports human proteins")

    submitted = st.form_submit_button("Submit Mapping")

    if submitted:
        try:
            conn = psycopg2.connect(
                dbname=st.secrets["DB_NAME"],
                user=st.secrets["DB_USER"],
                password=st.secrets["DB_PASS"],
                host=st.secrets["DB_HOST"],
                port=st.secrets["DB_PORT"]
            )
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO identifier_mappings (
                    source_database, target_database, identifier_type,
                    source_identifier_format, target_identifier_format,
                    translation_service_url, notes
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (source, target, id_type, src_format, tgt_format, url, notes))
            conn.commit()
            cursor.close()
            conn.close()
            st.success("✅ Mapping inserted successfully!")
        except Exception as e:
            st.error(f"❌ Error: {e}")

# -----------------------------------
# 2. CSV Upload
# -----------------------------------
st.markdown("---")
st.subheader("📤 Upload CSV to Insert Multiple Mappings")

file = st.file_uploader("Choose a CSV file", type=["csv"])

expected_columns = [
    "source_database", "target_database", "identifier_type",
    "source_identifier_format", "target_identifier_format",
    "translation_service_url", "notes"
]

if file is not None:
    df = pd.read_csv(file)
    st.write("🔍 Preview of Uploaded Data:")
    st.dataframe(df)

    missing = [col for col in expected_columns if col not in df.columns]
    extra = [col for col in df.columns if col not in expected_columns]

    if missing:
        st.warning(f"⚠️ Missing columns: {', '.join(missing)}. These fields will be saved as NULL.")
    if extra:
        st.info(f"ℹ️ Extra columns found: {', '.join(extra)}. They will be ignored.")

    df_filtered = df.reindex(columns=expected_columns)

    if st.button("Insert All Valid Rows"):
        try:
            conn = psycopg2.connect(
                dbname=st.secrets["DB_NAME"],
                user=st.secrets["DB_USER"],
                password=st.secrets["DB_PASS"],
                host=st.secrets["DB_HOST"],
                port=st.secrets["DB_PORT"]
            )
            cursor = conn.cursor()
            for _, row in df_filtered.iterrows():
                cursor.execute("""
                    INSERT INTO identifier_mappings (
                        source_database, target_database, identifier_type,
                        source_identifier_format, target_identifier_format,
                        translation_service_url, notes
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, tuple(row.fillna(None)))
            conn.commit()
            cursor.close()
            conn.close()
            st.success("✅ All valid rows inserted successfully!")
        except Exception as e:
            st.error(f"❌ Error inserting data: {e}")

# -----------------------------------
# 3. CSV Download
# -----------------------------------
st.markdown("---")
st.subheader("📥 Download Existing Mappings")

if st.button("Download CSV"):
    try:
        conn = psycopg2.connect(
            dbname=st.secrets["DB_NAME"],
            user=st.secrets["DB_USER"],
            password=st.secrets["DB_PASS"],
            host=st.secrets["DB_HOST"],
            port=st.secrets["DB_PORT"]
        )
        df = pd.read_sql("SELECT * FROM identifier_mappings", conn)
        csv = df.to_csv(index=False)
        st.download_button("Download as CSV", csv, "identifier_mappings.csv", "text/csv")
        conn.close()
    except Exception as e:
        st.error(f"❌ Error fetching data: {e}")
