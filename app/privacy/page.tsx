import React from "react";

export const metadata = {
  title: "Privacy Policy | Wholesale AI Chatbot",
};

export default function PrivacyPage() {
  return (
    <main className="mx-auto max-w-3xl px-6 py-10 space-y-6">
      <h1 className="text-2xl font-semibold">Privacy Policy / سياسة الخصوصية</h1>
      <section className="space-y-3 text-sm leading-relaxed">
        <p>
          <strong>English:</strong> We only process the data required to run the chat: the
          messages you send and basic Pi authentication data (user id & username
          provided by Pi Network). We do not sell or share your data with third
          parties. Session is maintained via a secure HTTP-only cookie. Images you
          upload are stored solely to generate responses or display back to you.
        </p>
        <p>
          <strong>العربية:</strong> نحن نعالج فقط البيانات اللازمة لتشغيل الدردشة: الرسائل التي
          ترسلها وبيانات المصادقة الأساسية من شبكة Pi (المعرف واسم المستخدم). لا
          نقوم ببيع بياناتك أو مشاركتها مع أطراف خارجية. يتم حفظ الجلسة عبر ملف
          كوكي آمن (HTTP-only). الملفات أو الصور التي ترفعها تُخزَّن فقط بهدف توليد
          الردود أو عرضها لك.
        </p>
        <p>
          <strong>Data Retention / الاحتفاظ بالبيانات:</strong> Messages may be temporarily
          cached for performance. You can request deletion by contacting support.
        </p>
        <p>
          <strong>Security / الأمان:</strong> Transport uses HTTPS in production. Avoid
          sharing any personal or sensitive information inside the chat.
        </p>
        <p>
          <strong>Updates / التحديثات:</strong> We may update this policy as the product
          evolves. Continued use after changes means you accept the new version.
        </p>
        <p>
          <strong>Contact / التواصل:</strong> For any privacy request email: example@yourapp.com
        </p>
      </section>
    </main>
  );
}
