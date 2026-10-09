// ============================================================
// إعدادات Firebase المشتركة - منصة المهندس محمد جمال عوض
//
// ملاحظة مهمة: databaseURL يشير إلى قاعدة بيانات مشروع
// "mohamedgamal11" بينما projectId هو "mgpro-2f83b".
// لو ظهر خطأ "إذن مرفوض"، عدّل قواعد (Rules) على المشروع
// الذي يملك قاعدة البيانات هذه فعلياً.
//
// ملاحظة أمنية: في بيئة إنتاج حقيقية لا تضع مفتاح API في
// ملفات عامة، واستخدم Firebase Authentication أو Cloud Functions.
// ============================================================
const firebaseConfig = {
    apiKey: "AIzaSyBO34EZgVpZquo1TWF52r47WujWZbqukFU",
    authDomain: "mgpro-2f83b.firebaseapp.com",
    databaseURL: "https://mohamedgamal11-default-rtdb.firebaseio.com",
    projectId: "mgpro-2f83b",
    storageBucket: "mgpro-2f83b.firebasestorage.app",
    messagingSenderId: "964974315895",
    appId: "1:964974315895:web:be64f714bab53dd6437972",
    measurementId: "G-5H1EQDFBRS"
};

if (!firebase.apps.length) {
    firebase.initializeApp(firebaseConfig);
}
const db = firebase.database();
