<script setup>
// We expect a full 'trek' object to be passed down from the dashboard
defineProps({
    trek: {
        type: Object,
        required: true
    },
    isBooked: {
        type: Boolean,
        default: false
    }
})
</script>

<template>
    <div class="trek-card p-4">
        <h3 class="mb-3">{{ trek.name }}</h3>
        
        <div class="info-grid mb-3">
            <p><strong>Location:</strong> {{ trek.location }}</p>
            <p><strong>Timeline:</strong> {{ trek.start_date }} to {{ trek.end_date }}</p>
            <p><strong>Difficulty:</strong> <span class="badge bg-dark">{{ trek.difficulty }}</span></p>
            <p><strong>Slots Left:</strong> <span class="text-success fw-bold">{{ trek.available_slots }}</span></p>
        </div>
        
        <button 
            :disabled="isBooked" 
            @click="$emit('book', trek.id)" 
            class="btn w-100 fw-bold"
            :class="isBooked ? 'btn-secondary' : 'btn-book'"
        >
            {{ isBooked ? 'Already Booked' : 'Request Booking' }}
        </button>
    </div>
</template>

<style scoped>
/* Lighter than the .neo-panel content area it sits inside, with its own
   crisper shadow pair — this is what actually makes it read as a card
   "floating" above the panel instead of blending into it. */
.trek-card {
    background: #ffffff;
    border: 1px solid rgba(255, 255, 255, 0.9);
    border-radius: 14px;
    box-shadow: 6px 6px 14px #c7d0c0, -6px -6px 14px #ffffff;
    transition: transform 0.3s ease, box-shadow 0.3s ease;
}

/* Hover Effect: The card physically "lifts" higher off the screen! */
.trek-card:hover {
    transform: translateY(-8px); /* Moves up 8 pixels */
    box-shadow: 10px 10px 22px #b7c0af, -10px -10px 22px #ffffff; /* Larger, darker shadow to sell the lift */
}

.info-grid p {
    margin-bottom: 5px;
    font-size: 0.95rem;
}

/* Forest-green accent instead of plain black, ties the card's CTA
   into the Trekker theme (kept distinct from Admin's blue). */
.btn-book {
    background-color: #3f6d52;
    color: #fff;
    border: none;
}
.btn-book:hover {
    background-color: #2f5940;
    color: #fff;
}
</style>