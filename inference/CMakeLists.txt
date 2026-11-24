idf_component_register(SRCS "inference.cpp"
                    INCLUDE_DIRS "."
                    EMBED_FILES "../ml/models/tinyintent_dynamic.tflite"
                    PRIV_REQUIRES espressif__esp-tflite-micro)
