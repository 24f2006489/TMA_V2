<script setup>
// defineProps tells Vue what data this component expects to receive from the parent page
defineProps({
    value: {
        type: [Number, String],
        required: true
    },
    label: {
        type: String,
        required: true
    },
    textColorClass: {
        type: String,
        default: 'text-dark' // e.g., 'text-primary', 'text-success'
    },
    borderClass: {
        type: String,
        default: '' // e.g., 'border-start border-4 border-primary' used in the Staff page
    }
})
</script>

<template>
    <div class="neo-card text-center p-4" :class="borderClass">
        <!-- We dynamically apply the color class to the number -->
        <h2 class="display-5 fw-bold" :class="textColorClass">{{ value }}</h2>
        <p class="text-muted fw-bold mb-0">{{ label }}</p>
    </div>
</template>

<style scoped>
/* Skeuomorphic CSS here so it only lives in ONE place! */
.neo-card {
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.9), rgba(248, 250, 252, 0.7));
    backdrop-filter: blur(10px); 
    border: 1px solid rgba(255, 255, 255, 0.8);
    border-radius: 15px;
    box-shadow: 6px 6px 12px #d1d9e6, -6px -6px 12px #ffffff;
    transition: transform 0.2s ease-in-out; 
    height: 100%; /* Ensures all cards in a row stretch to the same height */
}

.neo-card:hover {
    transform: translateY(-3px);
}
</style>