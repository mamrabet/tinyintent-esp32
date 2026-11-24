idf_component_register(SRCS "inference.cpp"
                    INCLUDE_DIRS "."
                    EMBED_FILES "../ml/models/tinyintent_dynamic_tflm.tflite"
                    PRIV_REQUIRES espressif__esp-tflite-micro)
