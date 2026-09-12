#!/bin/bash
sed -i 's/size="64"/size="55"/g' frontend/src/components/AddItemModal.vue
sed -i 's/style="width: 100%; height: 100%;"//g' frontend/src/components/AddItemModal.vue
sed -i 's/w-16 h-16/w-\[55px\] h-\[55px\] p-0/g' frontend/src/components/AddItemModal.vue
sed -i 's/p-2//g' frontend/src/components/AddItemModal.vue
